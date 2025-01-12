import re
from scrapy.exceptions import IgnoreRequest
from scrapy import signals
from ..proxy.proxy import FreeProxy


class URLFilterMiddleware:
    def __init__(self, patterns):
        self.patterns = [re.compile(pattern) for pattern in patterns]

    @classmethod
    def from_crawler(cls, crawler):
        # Load the regex patterns from settings
        patterns = crawler.settings.getlist('URL_FILTER_PATTERNS', [])
        return cls(patterns)

    def process_request(self, request, spider):
        for pattern in self.patterns:
            if pattern.search(request.url):
                spider.logger.info(f"Filtered URL: {request.url}")
                raise IgnoreRequest(f"URL {request.url} matches filter pattern {pattern.pattern}")
        return None


class ContentTypeFilterMiddleware:
    def __init__(self, allowed_content_types):
        self.allowed_content_types = allowed_content_types

    @classmethod
    def from_crawler(cls, crawler):
        # Load the allowed content types from settings
        allowed_content_types = crawler.settings.getlist('ALLOWED_CONTENT_TYPES', [])
        middleware = cls(allowed_content_types)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_response(self, request, response, spider):
        # Extract the Content-Type header
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').split(';')[0].strip()
        if content_type not in self.allowed_content_types:
            spider.logger.debug(f"Filtered out response with Content-Type: {content_type} for URL: {response.url}")
            raise IgnoreRequest(f"Content-Type {content_type} not allowed.")
        return response

    def spider_opened(self, spider):
        spider.logger.info("ContentTypeFilterMiddleware initialized.")


class Proxy:
    def __init__(self):
        self.proxy = FreeProxy(timeout=1, rand=True).get()
       
    def process_request(self, request, spider):
        if 'proxy' not in request.meta:
            request.meta['proxy'] = self.proxy