from CONFIG import VISITED_URLS_FILE
from proxy.proxy import FreeProxy

BOT_NAME = 'crawler'

DEPTH_LIMIT = 5

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

ROBOTSTXT_OBEY = True

# Log settings
LOG_ENABLED = True
LOG_LEVEL = 'DEBUG'  # 'INFO'

# Allowed Content-Type headers
ALLOWED_CONTENT_TYPES = ["text/html", "application/xhtml+xml"]

# Domain constraints 
ALLOWED_DOMAINS = ["ece.gatech.edu"]

# Seed URLS
SEED_URLS = ["https://ece.gatech.edu/"]

# Deny subdomains using regex patterns
URL_FILTER_PATTERNS = [
   r'/people.*', 
   r'/news.*', 
   r'/events.*', 
   r'mail', 
   r'calendar', 
   r'hcc'
   r'/node.*'
   r'/directory.*'
]

# Proxy
PROXY = FreeProxy(timeout=1, rand=True).get()

# JSON FILE NAME
NDJSON_FILE_NAME = VISITED_URLS_FILE

JOBDIR = 'crawler/crawls/crawler_state'

ITEM_PIPELINES = {
    'crawler.pipelines.NdjsonWriterPipeline': 300,
}

DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.URLFilterMiddleware': 543,
    'crawler.middlewares.ContentTypeFilterMiddleware': 544,  # Ignore everything but html files?
    #'crawler.middlewares.Proxy': 545,
}
