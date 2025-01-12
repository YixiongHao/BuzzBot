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
ALLOWED_DOMAINS = ["cc.gatech.edu"]

# Seed URLS
SEED_URLS = ["https://cc.gatech.edu/"]

# Deny subdomains using regex patterns
URL_FILTER_PATTERNS = [
   r'/people.*', 
   r'/news.*', 
   r'/events.*', 
   r'mail', 
   r'calendar', 
   r'hcc'
]

# Database Path
DB_PATH = "./database/data.db"  

JOBDIR = 'crawls/crawler_state'

ITEM_PIPELINES = {
   'crawler.pipelines.DataBasePipeline': 300,
}

DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.URLFilterMiddleware': 543,
    'crawler.middlewares.ContentTypeFilterMiddleware': 544,  # Ignore everything but html files?
      'crawler.middlewares.Proxy': 545,
}
