import json
import os


class NdjsonWriterPipeline:
    """
    Write each item to a file in NDJSON format (one valid JSON object per line),
    using the file path from a Scrapy setting (e.g. NDJSON_FILE_NAME).
    """

    def __init__(self, file_name):
        self.file_name = file_name
        self.file = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        A class method that Scrapy calls to create the pipeline.
        We read the NDJSON file name from the Scrapy settings (NDJSON_FILE_NAME).
        """
        ndjson_path = crawler.settings.get('NDJSON_FILE_NAME', 'crawled_links/visited_urls.json')
        return cls(ndjson_path)

    def open_spider(self, spider):
        """
        Called automatically when the spider starts.
        Opens the NDJSON file in append mode, ensuring directories exist.
        """
        # Ensure directories exist if the path includes subfolders
        os.makedirs(os.path.dirname(self.file_name), exist_ok=True)

        # Open the file in append mode so multiple runs can append
        self.file = open(self.file_name, "a", encoding="utf-8")

    def close_spider(self, spider):
        """
        Called automatically when the spider finishes.
        Closes the file.
        """
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        """
        Called for each item yielded by the spider.
        Convert item to JSON and write it as a single line (NDJSON).
        """
        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line + "\n")
        # Flush to disk immediately (optional)
        self.file.flush()
        return item
