import os
import logging
from dataclasses import dataclass
from typing import Dict, List, Any

import numpy as np
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from rich.console import Console

from langchainathome import EmbeddingProvider, SentenceTransformerEmbedding, GroqLLMProvider, OpenAILLMProvider

# Initialize logging and console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from CONFIG import ELASTICSEARCH_HOST, INDEX_NAME, LLM_PROVIDER, MAX_SEARCH_RESULTS

# Load environment variables
load_dotenv()


@dataclass
class FileMetadata:
    """Metadata for a file in the search index"""
    filename: str
    created: float
    path: str
    size: int
    extension: str


@dataclass
class SearchResult:
    """Results from a search or question answering operation"""
    result_type: str  # "answer" or "search"
    files: List[str]  # list of filenames for search results or sources for answers
    answer: str = ""  # answer for question, empty string if result_type is "search"


# Global cache for file metadata
file_metadata_cache: Dict[str, FileMetadata] = {}


class ElasticsearchClient:
    """Client for Elasticsearch operations"""
    
    def __init__(self):
        self.es = Elasticsearch(ELASTICSEARCH_HOST)
        if not self.es.ping():
            raise ConnectionError(f"Could not connect to Elasticsearch at {ELASTICSEARCH_HOST}")
        
    def _extract_file_metadata(self, hit: Dict[str, Any]) -> FileMetadata:
        """Extract file metadata from Elasticsearch hit"""
        source = hit["_source"]
        
        file_meta = FileMetadata(
            filename=source["filename"],
            created=source["created"],
            path=source.get("metadata", {}).get("path", ""),
            size=source.get("metadata", {}).get("size", 0),
            extension=source.get("metadata", {}).get("extension", "")
        )
        
        # Add to cache
        file_metadata_cache[file_meta.filename] = file_meta
        
        return file_meta
        
    def search_by_time_range(self, start_ts: float, end_ts: float) -> SearchResult:
        """Search for files within a time range"""
        resp = self.es.search(
            index=INDEX_NAME,
            query={"range": {"created": {"gte": start_ts, "lte": end_ts}}},
            size=MAX_SEARCH_RESULTS
        )
        
        files = []
        for hit in resp["hits"]["hits"]:
            self._extract_file_metadata(hit)
            files.append(hit["_source"]["filename"])
            
        return SearchResult(result_type="search", files=files)
    
    def semantic_search(self, query: str, embedding_provider: EmbeddingProvider) -> SearchResult:
        """Perform semantic search using both keyword matching and vector search"""
        query_embedding = embedding_provider.embed_text(query)
        
        resp = self.es.search(
            index=INDEX_NAME,
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
                "k": MAX_SEARCH_RESULTS,
                "num_candidates": MAX_SEARCH_RESULTS * 2,
            },
            size=MAX_SEARCH_RESULTS
        )
        
        files = []
        for hit in resp["hits"]["hits"]:
            self._extract_file_metadata(hit)
            files.append(hit["_source"]["filename"])
            
        return SearchResult(result_type="search", files=files)
    
    def retrieve_documents_for_qa(self, question: str, embedding_provider: EmbeddingProvider) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for question answering"""
        query_embedding = embedding_provider.embed_text(question)
        
        resp = self.es.search(
            index=INDEX_NAME,
            knn={
                "field": "vector",
                "query_vector": query_embedding,
                "k": 3,  # Retrieve top 3 most relevant documents
                "num_candidates": 5,
            },
            _source=["filename", "text", "created", "metadata"],
            size=3
        )
        
        documents = []
        for hit in resp["hits"]["hits"]:
            self._extract_file_metadata(hit)
            documents.append({
                "filename": hit["_source"]["filename"],
                "text": hit["_source"]["text"],
                "metadata": hit["_source"].get("metadata", {})
            })
            
        return documents


class SearchEngine:
    """Main search engine class that orchestrates search operations"""
    
    def __init__(self):
        # Initialize embedding provider based on configuration

        self.embedding_provider = SentenceTransformerEmbedding()

        # Initialize LLM provider based on configuration
        if LLM_PROVIDER == "groq":
            self.llm_provider = GroqLLMProvider()
        elif LLM_PROVIDER == "openai":
            self.llm_provider = OpenAILLMProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
        
        # Initialize Elasticsearch client
        self.es_client = ElasticsearchClient()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define the tools for the LLM to use"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_by_time_range",
                    "description": "Search for files created within a specific time range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_ts": {
                                "type": "number",
                                "description": "Start of the time range (in seconds since epoch)"
                            },
                            "end_ts": {
                                "type": "number",
                                "description": "End of the time range (in seconds since epoch)"
                            }
                        },
                        "required": ["start_ts", "end_ts"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "semantic_search",
                    "description": "Search for files using semantic and keyword matching",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "answer_question",
                    "description": "Generate an answer to a question based on the content of the files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to answer"
                            }
                        },
                        "required": ["question"]
                    }
                }
            }
        ]
    
    def answer_question(self, question: str) -> SearchResult:
        """Answer a question using the contents of relevant documents"""
        # Retrieve relevant documents
        documents = self.es_client.retrieve_documents_for_qa(question, self.embedding_provider)
        
        if not documents:
            return SearchResult(result_type="answer", files=[], answer="No relevant documents found to answer your question.")
        
        # Prepare context from documents
        context = "\n\n".join([f"Document: {doc['filename']}\n{doc['text']}" for doc in documents])
        
        # Prepare prompt for the LLM
        system_prompt = """You are a highly capable assistant designed to help with searching for files and answering questions about them. You have access to specialized tools for different types of queries. You always have to use at least one tool.
        
        You should use the question answering tool to provide information from the files returned by the semantic search tool that answers the query.
        
        When responding:
        - You have to use at least one tool.
        - Use the tools to obtain accurate results rather than estimating or computing manually.
        - If the query is ambiguous, make the best assumption and proceed with the search rather than asking for clarification.
        - Return tool outputs to the user without modifications if they appear correct.
        
        Your goal is to route each query to the most suitable tool and provide accurate, helpful responses based on the tool's output.
        """
        
        user_prompt = f"""Question: {question}
        
        Here are the relevant documents to help you answer:
        
        {context}"""
        
        # Generate answer using LLM
        response = self.llm_provider.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1  # Slight randomness for more natural answers
        )
        
        # Extract filenames of the documents used
        files = [doc["filename"] for doc in documents]
        
        return SearchResult(
            result_type="answer",
            files=files,
            answer=response["content"]
        )
    
    def route_query(self, query: str) -> SearchResult:
        """
        Route the query: if the input looks like a question (ends with '?'),
        use the question answering system; otherwise, perform a semantic search.
        """
        if query.strip().endswith("?"):
            return self.answer_question(query)
        else:
            return self.es_client.semantic_search(query, self.embedding_provider)

if __name__ == "__main__":
    search_engine = SearchEngine()
    query = input("Enter your query: ")
    result = search_engine.answer_question(query)

    if result.result_type == "answer":
        print("\nAnswer:\n", result.answer)
    else:
        print("\nSearch Results:")
        for filename in result.files:
            print(f"- {filename}")