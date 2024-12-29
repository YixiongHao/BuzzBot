from .db import DBHelper

class DataBasePipeline:
    def open_spider(self, spider):
        self.db = DBHelper(db_path="./database/data.db")
        self.db.open_connection()
        spider.db = self.db  # Attach db to spider for convenience

    def close_spider(self, spider):
        # Just close the connection if needed
        if self.db.conn:
            self.db.conn.close()

    def process_item(self, item, spider):
        # Not strictly required if we do insertion in the spider,
        # but you could do additional processing here if needed.
        return item