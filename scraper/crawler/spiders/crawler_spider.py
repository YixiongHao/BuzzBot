import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CrawlerSpider(CrawlSpider):
    name = "crawler_spider"
    allowed_domains = ["cc.gatech.edu"]
    start_urls = ["https://cc.gatech.edu/"]

    # Deny certain file extensions to avoid non-HTML resources
    deny_extensions = [
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx',
        'xls', 'xlsx', 'mp3', 'mp4', 'avi', 'wav', 'zip'
    ]

    deny_subdomains = [r'/people.*', r'/news.*', r'/events.*', r'mail', r'calendar', r'hcc']

    # Define rules to automatically follow links
    rules = (
        Rule(
            LinkExtractor(allow_domains=allowed_domains, deny_extensions=deny_extensions, deny=deny_subdomains),
            callback='parse_item', follow=True
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_key = "visited_urls"  # Key for storing visited URLs

    def start_requests(self):
        # Restore the visited URLs state
        self.state.setdefault(self.state_key, set())  # Initialize if not present

        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_item)
            
    def parse_item(self, response):
        # Just print out the URL of each visited page for demonstration
        # self.logger.info(f"Visited: {response.url}")

        parent_url = response.meta.get('parent_url')
        current_url = response.url

        # Insert current page and parent-child link if available
        self.db.insert_page(current_url)  # Ensure the current page exists in the database
        if parent_url:
            self.db.insert_link(parent_url, current_url)

        # Pass the current URL as the parent for child requests
        for link in LinkExtractor(allow_domains=self.allowed_domains, deny_extensions=self.deny_extensions, deny=self.deny_subdomains).extract_links(response):
            yield scrapy.Request(
                url=link.url,
                callback=self.parse_item,
                meta={'parent_url': current_url}
            )