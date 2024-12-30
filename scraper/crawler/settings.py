BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

ROBOTSTXT_OBEY = True
DEPTH_LIMIT = 5
LOG_ENABLED = True

JOBDIR = 'crawls/crawler_state'

LOG_LEVEL = 'INFO'

ITEM_PIPELINES = {
   'crawler.pipelines.DataBasePipeline': 300,
}