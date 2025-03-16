import asyncio
import time
import os
from typing import List, Dict, Any
import json
import logging
from pathlib import Path

import chainlit as cl
from chainlit.element import Element

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import search engine components
from search import SearchEngine, FileMetadata, SearchResult, file_metadata_cache

# Initialize the search engine
search_engine = SearchEngine()

def create_file_element(file_meta: FileMetadata) -> Element:
    """Create appropriate Chainlit element based on file extension"""
    extension_to_element = {
        ".pdf": cl.Pdf,
        ".txt": cl.Text,
        ".mp3": cl.Audio,
        ".jpg": cl.Image,
        ".jpeg": cl.Image,
        ".png": cl.Image,
        ".md": cl.Text,
    }
    
    # Get the element class based on file extension
    element_class = extension_to_element.get(file_meta.extension.lower())
    
    if element_class is None:
        # Default to Text for unsupported extensions
        logger.warning(f"Unsupported file extension: {file_meta.extension}, defaulting to Text element")
        element_class = cl.Text
    
    # Create and return the element
    try:
        return element_class(path=file_meta.path, name=file_meta.filename, display="side")
    except Exception as e:
        logger.error(f"Error creating element for {file_meta.filename}: {e}")
        # Create a fallback text element with information
        return cl.Text(
            content=f"File: {file_meta.filename}\nPath: {file_meta.path}\nSize: {file_meta.size} bytes",
            name=file_meta.filename,
            display="side"
        )

async def handle_search_request(user_input: str) -> None:
    """Process user search request asynchronously"""
    # Show thinking indicator
    await cl.Message(content="Searching through your documents...").send()
    
    # Use run_in_executor to run the CPU-bound search in a thread pool
    loop = asyncio.get_running_loop()
    search_results = await loop.run_in_executor(
        None, search_engine.route_query, user_input
    )
    
    # Handle empty search results
    if not search_results.files:
        await cl.Message(content="No results found matching your query.").send()
        return
    
    # Create elements for each file in the results
    elements = []
    for filename in search_results.files:
        if filename in file_metadata_cache:
            try:
                elements.append(create_file_element(file_metadata_cache[filename]))
            except Exception as e:
                logger.error(f"Error creating element for {filename}: {e}")
    
    # Build message content based on result type
    if search_results.result_type == "search":
        message_content = "## Search Results\n\n"
    else:  # answer
        message_content = f"## Answer\n\n{search_results.answer}\n\n### Sources\n\n"
    
    # Add metadata table
    message_content += "| File | Size | Created |\n|------|------|---------|\n"
    for filename in search_results.files:
        if filename in file_metadata_cache:
            file_meta = file_metadata_cache[filename]
            size_mb = f"{file_meta.size / (1024 * 1024):.2f} MB"
            created_dt = time.strftime("%Y-%m-%d %H:%M", time.localtime(file_meta.created))
            message_content += f"| {file_meta.filename} | {size_mb} | {created_dt} |\n"
    
    # Send the message with elements
    await cl.Message(content=message_content, elements=elements).send()

def parse_time_query(query: str) -> Dict:
    """Parse time-based queries like "files from last week" or "documents from yesterday"
    Returns start and end timestamps if it's a time-based query"""
    # This is a placeholder for natural language time parsing
    # Could be expanded with better NLP or regex patterns
    current_time = time.time()
    day_seconds = 24 * 60 * 60
    
    time_queries = {
        "today": (current_time - day_seconds, current_time),
        "yesterday": (current_time - 2 * day_seconds, current_time - day_seconds),
        "this week": (current_time - 7 * day_seconds, current_time),
        "last week": (current_time - 14 * day_seconds, current_time - 7 * day_seconds),
        "this month": (current_time - 30 * day_seconds, current_time),
        "last month": (current_time - 60 * day_seconds, current_time - 30 * day_seconds),
    }
    
    for time_phrase, (start_ts, end_ts) in time_queries.items():
        if time_phrase in query.lower():
            return {"start_ts": start_ts, "end_ts": end_ts}
    
    return None

async def process_query(user_input: str) -> None:
    """Process the query and determine which search method to use"""
    # Check if this is a time-based query
    time_range = parse_time_query(user_input)
    
    if time_range:
        # Use run_in_executor for time-based search
        loop = asyncio.get_running_loop()
        search_results = await loop.run_in_executor(
            None, 
            lambda: search_engine.es_client.search_by_time_range(time_range["start_ts"], time_range["end_ts"])
        )
    else:
        # Use the standard search routing mechanism
        search_results = await asyncio.get_running_loop().run_in_executor(
            None, search_engine.route_query, user_input
        )
    
    # Handle and present the results
    await present_results(search_results)

async def present_results(search_results: SearchResult) -> None:
    """Format and present search results to the user"""
    # Handle empty search results
    if not search_results.files:
        await cl.Message(content="No results found matching your query.").send()
        return
    
    # Create elements for each file in the results
    elements = []
    for filename in search_results.files:
        if filename in file_metadata_cache:
            try:
                elements.append(create_file_element(file_metadata_cache[filename]))
            except Exception as e:
                logger.error(f"Error creating element for {filename}: {e}")
    
    # Build message content based on result type
    if search_results.result_type == "search":
        message_content = "## Search Results\n\n"
        message_content += f"Found {len(search_results.files)} relevant document(s).\n\n"
    else:  # answer
        message_content = f"## Answer\n\n{search_results.answer}\n\n### Sources\n\n"
    
    # Add metadata table
    message_content += "| File | Size | Created |\n|------|------|---------|\n"
    for filename in search_results.files:
        if filename in file_metadata_cache:
            file_meta = file_metadata_cache[filename]
            size_mb = f"{file_meta.size / (1024 * 1024):.2f} MB"
            created_dt = time.strftime("%Y-%m-%d %H:%M", time.localtime(file_meta.created))
            message_content += f"| {file_meta.filename} | {size_mb} | {created_dt} |\n"
    
    # Send the message with elements
    await cl.Message(content=message_content, elements=elements).send()

@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! How can I assist you today?").send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    user_input = message.content
    
    async with cl.Step("Processing your search request...") as step:
        step.output = f"Processing: '{user_input}'"
        await process_query(user_input)

if __name__ == "__main__":
    cl.run()