import sqlite3
import pandas as pd
from parser import extractor

import os
import re


# Connect to the SQLite database
db_path = './database/ece.db' 
conn = sqlite3.connect(db_path)
links_df = pd.read_sql_query("SELECT * FROM links", conn)
pages_df = pd.read_sql_query("SELECT * FROM pages", conn)
conn.close()


def create_file(directory, title, content, write=False):
    """
    Creates a Markdown file with the given title and content.

    Parameters:
        directory (str): The directory where the file will be saved.
        title (str): The title of the Markdown file.
        content (str): The content of the Markdown file.
        write (bool): Whether to write the content to the file. Default is False.
    Returns:
        str: The filename of the created Markdown file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Create a sanitized filename from the title
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)  # Remove invalid characters
        sanitized_title = sanitized_title.strip() or "Untitled"  # Fallback to 'Untitled' if the title is empty
        filename = os.path.join(directory, f"{sanitized_title}.md")

        # Write content to the file
        if write:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)

        return filename

    except Exception as e:
        return f"Error creating file: {e}"


def bfs(links, pages, start_node, max_depth):
    visited = set()
    queue = [(start_node, 0)]  # Store nodes as (node, depth)
    traversal_order = []

    # Create a dictionary to map node IDs to URLs for quick lookup
    url_map = {row['id']: row['url'] for _, row in pages.iterrows()}

    print(f"Starting BFS Traversal from Node {start_node} (Depth Limit: {max_depth}):\n")
    while queue:
        current_node, current_depth = queue.pop(0)

        if current_node not in visited and current_depth <= max_depth:
            visited.add(current_node)
            traversal_order.append(current_node)

            # Print the current node and its corresponding URL
            url = url_map.get(current_node, "URL not found")
            title, content = extractor(url)
            file = create_file("./downloader/files", title, content, write=False)

            print(f"Node: {current_node} \t Depth: {current_depth} \t File: {file}")

            # Get children of the current node
            if current_depth < max_depth:  # Only add children if below the depth limit
                children = links[links['parent_id'] == current_node]['child_id'].tolist()
                queue.extend((child, current_depth + 1) for child in children)
    
    return traversal_order

# Define the maximum depth limit
max_depth = 2

# Start BFS from node 1 with a depth limit
bfs_order = bfs(links_df, pages_df, 1, max_depth)

# Print the BFS traversal result
print("\nBFS Traversal Order (Node IDs):", bfs_order)
