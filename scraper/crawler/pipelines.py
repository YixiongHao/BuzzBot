from .db import DBHelper

class DataBasePipeline:
    def open_spider(self, spider):
        # Retrieve db_path from settings
        db_path = spider.settings.get("DB_PATH", "./database/data.db")  # Default path if not set
        self.db = DBHelper(db_path=db_path)
        self.db.open_connection()
        spider.db = self.db  # Attach db to spider for convenience

    def close_spider(self, spider):
        # Close the database connection
        if self.db.conn:
            self.db.conn.close()

    def process_item(self, item, spider):
        # Perform any additional processing if needed
        return item
