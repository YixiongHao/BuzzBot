import os
import time
import warnings
from typing import Callable, List

import numpy as np
import pytesseract
import rich
import whisper
from elasticsearch import Elasticsearch

from CONFIG import ELASTICSEARCH_HOST, INDEX_NAME

ES = Elasticsearch(ELASTICSEARCH_HOST)
INDEX = INDEX_NAME

def verify_index_contents():
    """
    Print a summary of the documents in the Elasticsearch index.
    """
    # Refresh the index to ensure all documents are searchable
    ES.indices.refresh(index=INDEX)
    
    # Get total number of documents
    count = ES.count(index=INDEX)['count']
    print(f"\nTotal documents indexed: {count}")
    
    # Get a sample of documents
    results = ES.search(
        index=INDEX,
        body={
            "query": {"match_all": {}},
            "size": 10,  # Adjust this number to see more/fewer documents
            "_source": ["filename", "text"]  # Only return these fields
        }
    )
    
    print("\nSample of indexed documents:")
    for hit in results['hits']['hits']:
        print(f"\nFilename: {hit['_source']['filename']}")
        print(f"Text preview: {hit['_source']['text'][:200]}...")  # Show first 200 characters

if __name__ == "__main__":
    verify_index_contents()  # Add this line to run the verification