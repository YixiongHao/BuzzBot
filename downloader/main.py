import json
import os
import re
import requests
import html2text
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from CONFIG import VISITED_URLS_FILE, DOWNLOADED_FILES_DIR, CHECKPOINT_FILE_NAME


'''
PARSER
'''
def extractor(url):
    """
    Fetches the title and content of a webpage and converts the content to Markdown.

    Parameters:
        url (str): The URL of the webpage.

    Returns:
        tuple: A tuple containing the title (str) and Markdown content (str).
    """
    try:
        # Fetch the HTML content
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        # Extract the title using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "Untitled"

        # Convert HTML to Markdown
        converter = html2text.HTML2Text()
        converter.ignore_links = True  # Keep links
        converter.ignore_images = True  # Keep images
        converter.bypass_tables = False  # Convert tables

        markdown_content = converter.handle(html_content)
        return title, markdown_content

    except requests.RequestException as e:
        return "Error", f"Error fetching the URL: {e}"
    except Exception as e:
        return "Error", f"Error processing the content: {e}"


def create_file(directory, title, content, write=True):
    """
    Creates a Markdown file with the given title and content.
    Returns the filename or an error message.
    """
    try:
        os.makedirs(directory, exist_ok=True)

        # Remove invalid characters for filenames
        sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
        sanitized_title = sanitized_title.strip() or "Untitled"
        filename = os.path.join(directory, f"{sanitized_title}.md")

        if write:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

        return filename
    except Exception as e:
        return f"Error creating file: {e}"


def read_checkpoint(checkpoint_file):
    """
    Reads the last processed line number from checkpoint_file.
    Returns 0 if the file doesn't exist or is invalid.
    """
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            line_str = f.read().strip()
            if line_str.isdigit():
                return int(line_str)
    return 0


def write_checkpoint(checkpoint_file, line_number):
    """
    Writes the given line_number to checkpoint_file.
    Overwrites the file each time.
    """
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        f.write(str(line_number))
        f.flush()


def trim_markdown_file(filename, title, footer_filter):
    """
    Trims the Markdown file by:
    1. Removing all content above the first markdown title heading (#) that contains parts of the title.
       If no such header is found, trims above the first markdown title heading regardless of its content.
    2. Removing the footer filter line ("### Georgia Institute of Technology") and everything after it.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Prepare parts of the title (split into words)
        title_parts = re.findall(r'\w+', title)
        if not title_parts:
            print(f"No valid title parts found in title: '{title}'")
            return

        # Create a regex pattern to match any of the title parts in a header
        pattern_specific = re.compile(
            r'^#\s+.*(' + '|'.join(re.escape(part) for part in title_parts) + r').*',
            re.IGNORECASE
        )

        # Create a regex pattern to match any markdown title header
        pattern_fallback = re.compile(r'^#\s+.*', re.IGNORECASE)

        # Initialize variables to track indices
        start_index = None

        # 1. Trim the top content

        # First, try to find the specific header
        for i, line in enumerate(lines):
            if pattern_specific.match(line):
                start_index = i
                print(f"Found specific title header at line {i + 1} in '{filename}'.")
                break

        # If specific header not found, try to find any title header
        if start_index is None:
            for i, line in enumerate(lines):
                if pattern_fallback.match(line):
                    start_index = i
                    print(f"Specific title header not found. Using fallback header at line {i + 1} in '{filename}'.")
                    break

        if start_index is not None:
            # Keep content from the matching header onwards
            trimmed_lines = lines[start_index:]
            print(f"Trimmed top content in '{filename}' starting from line {start_index + 1}.")
        else:
            # No header found; keep the entire content
            trimmed_lines = lines
            print(f"No markdown title header found in '{filename}'. No top trimming performed.")

        # 2. Trim the footer content

        # Search for the footer filter line
        footer_index = None
        for i, line in enumerate(trimmed_lines):
            if line.strip() == footer_filter:
                footer_index = i
                print(f"Found footer filter at line {i + 1} in '{filename}'. Trimming footer.")
                break

        if footer_index is not None:
            # Keep content up to the footer filter line (exclude footer and below)
            trimmed_lines = trimmed_lines[:footer_index]
            print(f"Trimmed footer content in '{filename}' up to line {footer_index}.")
        else:
            print(f"No footer filter found in '{filename}'. No footer trimming performed.")

        # Write the trimmed content back to the file
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(trimmed_lines)
        print(f"Successfully trimmed '{filename}'.\n")

    except Exception as e:
        print(f"Error trimming file '{filename}': {e}")


def download_serially_by_line(ndjson_file, download_dir, checkpoint_file):
    """
    Reads each line in the NDJSON file in order, downloads `current_url`, and saves
    (title, content) to a markdown file. Stores the last processed line in `checkpoint_file`
    so we can resume from the next line if interrupted.
    """
    # 1. Determine which line we left off on
    start_line = read_checkpoint(checkpoint_file)
    line_number = 0

    print(f"Resuming from line {start_line} in {ndjson_file}.")

    # 2. Open the NDJSON for reading
    with open(ndjson_file, "r", encoding="utf-8") as f:
        for line in f:
            # If we haven't reached our resume point yet, skip
            if line_number < start_line:
                line_number += 1
                continue

            line = line.strip()
            if not line:
                line_number += 1
                continue  # skip empty lines

            # Attempt to parse JSON
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Line {line_number}: Invalid JSON, skipping...")
                line_number += 1
                continue

            current_url = record.get("current_url")
            if not current_url:
                print(f"Line {line_number}: No 'current_url' field, skipping...")
                line_number += 1
                continue

            # 3. Download (extract) the page
            print(f"Line {line_number}: Downloading {current_url}")
            title, content = extractor(current_url)  # your custom function

            # 4. Create the markdown file from the extracted content
            md_file = create_file(download_dir, title, content, write=True)
            print(f"--> Created {md_file}")

            # 5. Trim the markdown file as per requirements
            if isinstance(md_file, str) and not md_file.startswith("Error"):
                trim_markdown_file(md_file, title, "### Georgia Institute of Technology")

            # 6. Update our checkpoint to the *next* line
            line_number += 1
            write_checkpoint(checkpoint_file, line_number)


def main():
    # NDJSON file with lines of {"parent_url": ..., "current_url": ...}
    ndjson_file = VISITED_URLS_FILE
    download_dir = DOWNLOADED_FILES_DIR  # Change this to an absolute path outside. 
    checkpoint_file = CHECKPOINT_FILE_NAME

    download_serially_by_line(ndjson_file, download_dir, checkpoint_file)


if __name__ == "__main__":
    main()
