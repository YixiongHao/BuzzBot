import sqlite3
from typing import Optional

class DBHelper:
    def __init__(self, db_path="crawler.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def open_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.create_tables()
    
    def create_tables(self):
        # Create pages table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            );
        ''')
        # Create links table (edges)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS links (
                parent_id INTEGER,
                child_id INTEGER,
                FOREIGN KEY(parent_id) REFERENCES pages(id),
                FOREIGN KEY(child_id) REFERENCES pages(id),
                UNIQUE(parent_id, child_id)
            );
        ''')
        self.conn.commit()

    def get_page_id(self, url: str) -> Optional[int]:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM pages WHERE url = ?", (url,))
        row = cur.fetchone()
        return row[0] if row else None

    def insert_page(self, url: str) -> int:
        page_id = self.get_page_id(url)
        if page_id is None:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO pages (url) VALUES (?)", (url,))
            self.conn.commit()
            return cur.lastrowid
        return page_id

    def insert_link(self, parent_url: str, child_url: str):
        parent_id = self.insert_page(parent_url)
        child_id = self.insert_page(child_url)
        # Insert the link if it doesn't exist
        try:
            self.conn.execute("INSERT INTO links (parent_id, child_id) VALUES (?,?)",
                              (parent_id, child_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Link already exists
            pass

    def has_visited(self, url: str) -> bool:
        return self.get_page_id(url) is not None
