BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

ROBOTSTXT_OBEY = True
DEPTH_LIMIT = 5
LOG_ENABLED = True

JOBDIR = 'crawls/crawler_state'

# EXTENSIONS = {
#     'scrapy.extensions.spiderstate.SpiderState': 500,  # Enable SpiderState
# }

ITEM_PIPELINES = {
   'crawler.pipelines.DataBasePipeline': 300,
}