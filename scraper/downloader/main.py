import json
import os
import re
from parser import extractor


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

            # 5. Update our checkpoint to the *next* line
            line_number += 1
            write_checkpoint(checkpoint_file, line_number)


def main():
    # NDJSON file with lines of {"parent_url": ..., "current_url": ...}
    ndjson_file = "./crawled_links/visited_urls.json"
    download_dir = "downloader/files"
    checkpoint_file = "downloader/files/checkpoint.txt"

    download_serially_by_line(ndjson_file, download_dir, checkpoint_file)


if __name__ == "__main__":
    main()
