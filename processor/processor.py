import os
import time
import warnings
from typing import Callable, List

import numpy as np
import pytesseract
import rich
import whisper
from elasticsearch import Elasticsearch
from pdf2image import convert_from_path
from PIL import Image
from rich.progress import Progress, TaskID
from sentence_transformers import SentenceTransformer
from transformers import BlipForConditionalGeneration, BlipProcessor

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# This is just for illustration purposes.
# Expand the list to include more extensions and update the process_file function as needed.
VALID_FILE_EXTENSIONS = [".pdf", ".mp3", ".txt", ".png", ".jpg", ".jpeg"]

SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = SBERT_MODEL.encode("random").shape[0]

WHISPER_MODEL = whisper.load_model("base")

BLIP_PROCESSOR = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
BLIP_MODEL = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

# Elasticsearch
ES = Elasticsearch("http://localhost:3000/")
INDEX = "nls_search_final"

# To make the index compatible with LangChain's QA chain, besides indexing each field separately,
# we also index them together as a single field called "metadata"
# and embedding, we will use the name "vector".
INDEX_MAPPING = {
    "properties": {
        "filename": {"type": "text", "analyzer": "english"},
        "text": {"type": "text", "analyzer": "english"},
        "created": {"type": "double"},
        "vector": {
            "type": "dense_vector",
            "dims": EMBEDDING_DIM,
            "index": True,  # required for similarity search
            "similarity": "cosine",
        },
        "metadata": {"type": "object", "enabled": False},
    }
}


def get_embedding(text: str, token_limit=512) -> np.ndarray:
    """
    Get the embedding of the text using the SBERT model.
    """
    words = text.split()
    n = len(words)//token_limit + 1
    embedding = np.zeros(384)
    for i in range (n):
        if i == n-1:
            chunk = words[i*token_limit:]
        else:
            chunk = words[i*token_limit:(i+1)*token_limit]
        chunk_text = ' '.join(chunk)
        chunk_embedding = SBERT_MODEL.encode(chunk_text)
        embedding = np.add(embedding, chunk_embedding)
    embedding = np.divide(embedding, n)
    return embedding


def get_files_in_folder(folder_path: str) -> List[str]:
    """
    Get a list of all files within the specified folder.
    """
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def index_file(text: str, metadata: dict, embedding: np.ndarray):
    ES.index(
        index=INDEX,
        body={
            "filename": metadata["filename"],
            "text": text,
            "created": metadata["created"],
            "vector": embedding,
            "metadata": metadata,
        },
    )


def process_file(file_path: str) -> bool:
    """
    Process a single file. Returns True if the file was processed successfully, False otherwise.
    """
    time.sleep(1)
    # Your file processing logic goes here
    if not file_path.lower().endswith(tuple(VALID_FILE_EXTENSIONS)):
        rich.print(f"[yellow]Skipping file: {file_path}[/yellow]")
        return False

    rich.print(f"[blue]Processing file: {file_path}[/blue]")

    # Get basic file metadata
    file_stats = os.stat(file_path)
    file_metadata = {
        "filename": os.path.basename(file_path),
        "path": file_path,
        # TODO: Due to a bug on MacOS, we use the last modified time instead of the creation time.
        # which is good enough for demo purposes.
        "created": os.path.getmtime(file_path),
        "size": file_stats.st_size,
        "extension": os.path.splitext(file_path)[1].lower(),
    }

    text = ""
    if file_metadata["extension"] in [".txt"]:
        # Pure text files
        with open(file_path, "r") as f:
            text = f.read()
    elif file_metadata["extension"] in [".mp3"]:
        # Audio files
        text = WHISPER_MODEL.transcribe(file_path)["text"]
    elif file_metadata["extension"] in [".png", ".jpg", ".jpeg"]:
        # We get both the image description and the image caption, and concatenate them
        image = Image.open(file_path).convert("RGB")

        # Get the image description
        inputs = BLIP_PROCESSOR(image, return_tensors="pt")
        out = BLIP_MODEL.generate(**inputs, max_new_tokens=400)
        description = BLIP_PROCESSOR.decode(out[0], skip_special_tokens=True)

        # Get the image caption
        ocr_result = pytesseract.image_to_string(image)
        text = f"{description}\n{ocr_result}"
    elif file_metadata["extension"] in [".pdf"]:
        # PDF files
        pages = convert_from_path(file_path)
        pdf_page_texts = [
            pytesseract.image_to_string(page.convert("RGB")) for page in pages
        ]
        text = "\n".join(pdf_page_texts)
    else:
        raise ValueError(f"Unsupported file extension: {file_metadata['extension']}")

    embedding = get_embedding(text)
    index_file(text, file_metadata, embedding)

    ES.indices.refresh(index=INDEX)

    return True


def process_files(folder_path: str):
    """
    Process all files in the specified folder using the given process function.
    """
    files = get_files_in_folder(folder_path)
    skipped = []

    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files))

        for file_path in files:
            success = process_file(file_path)
            if not success:
                skipped.append(file_path)
            progress.update(task, advance=1)

    rich.print(f"[yellow]Skipped {len(skipped)} files.[/yellow]")
    rich.print("[green bold]Done[/green bold]")


if __name__ == "__main__":
    folder_path = input("Please enter the folder path: ")

    # Remove the index if it exists, always overwrite the index
    if ES.indices.exists(index=INDEX):
        ES.indices.delete(index=INDEX)

    ES.indices.create(index=INDEX, mappings=INDEX_MAPPING)

    # trim the quotes from the folder path (single quote or double quote)
    folder_path = folder_path.strip('"')
    folder_path = folder_path.strip("'")

    process_files(folder_path)
