import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import os


class CrawlerSpider(CrawlSpider):
    name = "crawler_spider"

    # Initialize as empty; will be set in from_crawler
    allowed_domains = []
    start_urls = []

    # Define rules as an empty tuple; will be set in from_crawler
    rules = ()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CrawlerSpider, cls).from_crawler(crawler, *args, **kwargs)
        
        # Retrieve allowed_domains and start_urls from settings
        spider.allowed_domains = crawler.settings.getlist('ALLOWED_DOMAINS')
        spider.start_urls = crawler.settings.getlist('SEED_URLS')

        # Define rules with LinkExtractor using allowed_domains
        spider.rules = (
            Rule(
                LinkExtractor(allow_domains=spider.allowed_domains),
                callback='parse_item',
                follow=True
            ),
        )
        
        # Compile the rules
        spider._compile_rules()

        # Key for storing visited URLs
        spider.state_key = "visited_urls"

        return spider

    def start_requests(self):
        # Restore the visited URLs state
        self.state.setdefault(self.state_key, set())  # Initialize if not present

        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_item)

    def parse_item(self, response):
        # Log the URL of each visited page
        self.logger.info(f"Visited: {response.url}")

        parent_url = response.meta.get('parent_url')
        current_url = response.url

        # Yield item as dict; pipeline writes NDJSON
        yield {
            "parent_url": parent_url,
            "current_url": current_url
        }

        # Pass the current URL as the parent for child requests
        for link in LinkExtractor(allow_domains=self.allowed_domains).extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_item,
                meta={'parent_url': current_url}
            )
