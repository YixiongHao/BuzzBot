import os
import time
from dataclasses import dataclass

import numpy as np
import rich
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools.render import format_tool_to_openai_function
from langchain_core.embeddings import Embeddings
from langchain_elasticsearch import DenseVectorScriptScoreStrategy, ElasticsearchStore
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

ES = Elasticsearch("http://localhost:9200/")
SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX = "nls_search_final"


@dataclass
class File:
    filename: str
    created: float
    path: str
    size: int
    extension: str


@dataclass
class NLSResult:
    result_type: str  # "answer" or "search"
    # list of filenames for search results or sources for answers
    # NOTE: we don't use list[File] because we want to keep the result type simple enough as the output of tools
    # so that it's easier for LLM to parse
    # we keep a mapping from filename to File object separately.
    files: list[str]
    answer: str  # answer for question, empty string if result_type is "search"


# Serve as a cache for File objects
# Everytime we get a search result, we add the File objects to this cache.
# For simplicity, we don't invalidate the cache.
file_by_name: dict[str, File] = {}


def time_ranged_search(start_ts: float, end_ts: float) -> list[str]:
    resp = ES.search(
        index=INDEX, query={"range": {"created": {"gte": start_ts, "lte": end_ts}}}
    )

    files: list[str] = []
    for hit in resp["hits"]["hits"]:
        # Add to cache
        file_by_name[hit["_source"]["filename"]] = File(
            filename=hit["_source"]["filename"],
            created=hit["_source"]["created"],
            path=hit["_source"]["metadata"]["path"],
            size=hit["_source"]["metadata"]["size"],
            extension=hit["_source"]["metadata"]["extension"],
        )

        # Add to result
        files.append(hit["_source"]["filename"])

    return NLSResult(result_type="search", files=files, answer="")


@tool
def get_time_ranged_search_results(start_ts: float, end_ts: float) -> NLSResult:
    """
    Returns search results between two Unix timestamps.

    Parameters:
    - start_ts (float): Start of the time range (in seconds since epoch). Default is 0
    - end_ts (float): End of the time range (in seconds since epoch).

    Notes:
    - Both `start_ts` and `end_ts` are required. Do not use the current timestamp as `end_ts` unless specified.
    - For queries like "files created in 2021", compute `start_ts` as the beginning of 2021 and `end_ts` as the end of 2021.

    Example:
    - get_time_ranged_search_results(1609459200.0, 1640995199.0) for "files created in 2021".
    """
    return time_ranged_search(start_ts, end_ts)


def semantic_search(query: str) -> NLSResult:
    query_embedding = SBERT_MODEL.encode([query])[0]
    resp = ES.search(
        index=INDEX,
        query={
            "bool": {
                "should": [
                    {"match": {"filename": {"query": query, "fuzziness": "auto"}}},
                    {"match": {"text": {"query": query, "fuzziness": "auto"}}},
                ]
            }
        },
        knn={
            "field": "vector",
            "query_vector": query_embedding,
            "k": 1,
            "num_candidates": 3,
        },
    )

    files: list[str] = []
    for hit in resp["hits"]["hits"]:
        # Add to cache
        file_by_name[hit["_source"]["filename"]] = File(
            filename=hit["_source"]["filename"],
            created=hit["_source"]["created"],
            path=hit["_source"]["metadata"]["path"],
            size=hit["_source"]["metadata"]["size"],
            extension=hit["_source"]["metadata"]["extension"],
        )

        # Add to result
        files.append(hit["_source"]["filename"])

    return NLSResult(result_type="search", files=files, answer="")


@tool
def get_semantic_search_results(query: str) -> NLSResult:
    """
    Returns search results for a semantic query that does not involve time ranges.
    Example:
    - get_semantic_search_results("christmas hat")
    """
    return semantic_search(query)


class SbertEmbedding(Embeddings):
    """
    Embedding function for SBERT model.
    By creating a custom Embeddings class, we can reuse the same embedding function for the QA chain.
    Otherwise, with HuggingFaceEmbeddings(), we would have to keep two copies of the embedding model in memory.

    The following methods are required by the Embeddings class but we actually only care about `embed_query` .
    """

    def embed_query(self, query: str) -> list[float]:
        return SBERT_MODEL.encode(query).tolist()

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        return [SBERT_MODEL.encode(doc).tolist() for doc in documents]


def answer_question(question: str) -> NLSResult:
    """
    Returns answers for a question about the file contents.
    """
    # Setup ElasticsearchStore
    es_store = ElasticsearchStore(
        es_url="http://localhost:9200",
        index_name=INDEX,
        embedding=SbertEmbedding(),
        strategy=DenseVectorScriptScoreStrategy(),
    )

    # Setup llm to use
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0.1, openai_api_key=openai_api_key)

    # Setup QA chain
    qa = RetrievalQA.from_chain_type(
        chain_type="stuff",  # -> fill up
        llm=llm,
        retriever=es_store.as_retriever(
            search_kwargs={"k": 1},  # Right now, we only keep one file as the source
        ),
        return_source_documents=True,
    )

    # Invoke QA chain
    resp = qa.invoke(question)

    answer = resp["result"]
    files: list[str] = []
    for doc in resp["source_documents"]:
        # Add to cache
        file_by_name[doc.metadata["filename"]] = File(
            filename=doc.metadata["filename"],
            created=doc.metadata["created"],
            path=doc.metadata["path"],
            size=doc.metadata["size"],
            extension=doc.metadata["extension"],
        )

        # Add to result
        files.append(doc.metadata["filename"])

    return NLSResult(result_type="answer", files=files, answer=answer)


@tool
def get_answers_for_question(question: str) -> NLSResult:
    """
    Returns answers for a question about the file contents.
    """
    return answer_question(question)


SYSTEM_PROMPT = """You are a highly capable assistant designed to help with searching for files and answering questions about them. You have access to specialized tools for different types of queries. You always have to use at least one tool.

1. For questions about file contents:
   Use the question answering tool to provide information from the files. This is usually indicated by a ending question mark (?) in the query.

2. For time-ranged queries (involving dates or times):
   Use the time-ranged search tool. Remember that the current Unix timestamp is {current_time}.
   Avoid performing time calculations yourself; use the provided tools for accuracy.

3. For semantic queries (general search without time constraints):
   Use the semantic search tool to find relevant files based on content or keywords. A semantic query does not contain a question mark (?) in the end. 
   Only use this tool if the query does not fit into any of the above categories.

When responding:
- Analyze the query to determine which tool is most appropriate, starting with the question answering tool, then the time-ranged search tool, and finally the semantic search tool.
- You have to use at least one tool.
- Use the tools to obtain accurate results rather than estimating or computing manually.
- For time-ranged searches, ensure you pass properly computed timestamps (as floats representing Unix time) to the tools.
- If unsure about any calculation or process, use the appropriate tool to achieve the desired outcome.
- Return tool outputs to the user without modifications if they appear correct.

Your goal is to route each query to the most suitable tool and provide accurate, helpful responses based on the tool's output.
"""


def natural_language_search(query: str) -> tuple[NLSResult, dict[str, File]]:
    """
    Returns a tuple of (NLSResult, dict[str, File]).
    The File dict contians the mapping from filename to File object that are relevant to the result.
    """
    tools = [
        get_answers_for_question,  # to answer questions about the file contents
        # TODO: Consider combining these two tools into a single tool that can perform both time-ranged and semantic search.
        get_time_ranged_search_results,  # to perform time-ranged search
        get_semantic_search_results,  # to perform semantic search
        PythonREPLTool(),  # to execute python code, for doing math
    ]

    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
    llm_with_tools = llm.bind(
        functions=[format_tool_to_openai_function(tool) for tool in tools]
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT.format(current_time=int(time.time()))),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_functions(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIFunctionsAgentOutputParser()
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    result = agent_executor.invoke({"input": query})

    # Uncomment this for debugging
    # rich.print(result)

    search_result = result["intermediate_steps"][-1][-1]

    try:
        if search_result.result_type == "search":
            # Filter out the search result that the LLM chose to return in the final response
            # This helps perform file type filtering in the final response
            search_result.files = [
                r for r in search_result.files if r in result["output"]
            ]
        elif search_result.result_type not in ["search", "answer"]:
            # This should never happen
            raise ValueError(f"Invalid result type: {search_result.result_type}")

        file_metas = {
            fname: f
            for fname, f in file_by_name.items()
            if fname in search_result.files
        }

        return search_result, file_metas
    except Exception as e:
        rich.print(e)
        raise e
