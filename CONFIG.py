'''
A file to store all the USEFUL variables that span multiple files.
'''
# APP : search.py
# PROCESSOR : processor.py
# PROCESSOR : verify_index.py
ELASTICSEARCH_HOST = "http://localhost:9200/"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_NAME = "nls_search_final"

# PROCESSOR : processor.py
PYTESSERACT_PATH = r'C:\Users\Yixio\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
PROCESSORED_FOLDER_PATH = ""  # Is this the downloaded_file dir from the scraper?

# SCRAPER/CRAWLER : settings.py
# SCRAPER/DOWNLOADER : main.py
# SCRAPER/VISUALISE : visualiser.py
VISITED_URLS_FILE = "crawled_links/visited_urls.json"
DOWNLOADED_FILES_DIR = "downloader/files"
CHECKPOINT_FILE_NAME = "downloader/files/checkpoint.txt"

