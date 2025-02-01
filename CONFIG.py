'''
A file to store all the USEFUL variables that span multiple files.

TODO: Currently, it is just a list of variables used. Actually make it syntactically correct.
'''
# APP : search.py
ES = Elasticsearch("http://localhost:9200/")
SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX = "nls_search_final"

# PROCESSOR : processor.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Yixio\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
ES = Elasticsearch("http://localhost:9200/")
SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
INDEX = "nls_search_final"
folder_path = input("Please enter the folder path: ")

# PROCESSOR : verify_index.py
ES = Elasticsearch("http://localhost:9200/")
INDEX = "nls_search_final"

# SCRAPER/CRAWLER : settings.py
NDJSON_FILE_NAME = "crawled_links/visited_urls.json"

# SCRAPER/DOWNLOADER : settings.py
ndjson_file = "./crawled_links/visited_urls.json"
download_dir = "downloader/files"  # Change this to an absolute path outside. 
checkpoint_file = "downloader/files/checkpoint.txt"

# SCRAPER/VISUALISE : visualiser.py
NDJSON_FILE = "./crawled_links/visited_urls.json"  # Path to your NDJSON file