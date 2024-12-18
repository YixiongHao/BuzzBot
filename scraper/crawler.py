'''
TODO:
- Generalize the crawler filter so it is not hard-coded to gatech.edu.
- Add some heuristic to determine if a page is useful or not.
    - The more useful, the more depth should be searched.
'''

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import sqlite3


class Crawler:
    def __init__(self, url=None, db_file=None, max_depth=2):
        '''
        Initialize the crawler.

        :param url: str, the starting url
        :param file: str, the name of the file to a prior checkpoint
        :param depth: int, the maximum depth of the search
        :param breadth: int, the maximum breadth of the search
        '''
        self.url = url
        self.db_file = db_file
        self.depth = max_depth

        self.conn = sqlite3.connect(self.db_file)
        self.conn.execute("PRAGMA journal_mode = wal;")  # For concurrent access/performance
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.init_db()

        # If we have a seed_url and it's not already in the DB, insert it
        if self.url:
            self.insert_seed(self.url)
    
    def init_db(self):
        """
        Initialize the database and create tables if they don't exist.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT PRIMARY KEY,
            crawled INTEGER NOT NULL,
            parent TEXT,
            depth INTEGER NOT NULL
        );
        """
        self.conn.execute(create_table_sql)
        self.conn.commit()

    def insert_seed(self, url):
        """
        Insert the seed URL if not already present.
        """
        # Check if seed exists
        cur = self.conn.cursor()
        cur.execute("SELECT url FROM pages WHERE url = ?", (url,))
        row = cur.fetchone()
        if row is None:
            # Insert seed
            cur.execute("INSERT INTO pages (url, crawled, parent, depth) VALUES (?, ?, ?, ?)",
                        (url, 0, None, 0))
            self.conn.commit()

    def insert_page(self, url, parent, depth):
        """
        Insert a new page into the database if it doesn't already exist.

        :param url: str, the URL of the page
        :param parent: str, the parent URL
        :param depth: int, the depth of the page relative to the seed URL
        """
        cur = self.conn.cursor()
        # Check if it exists
        cur.execute("SELECT url FROM pages WHERE url = ?", (url,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO pages (url, crawled, parent, depth) VALUES (?, ?, ?, ?)",
                        (url, 0, parent, depth))
            self.conn.commit()

    def mark_crawled(self, url):
        """
        Mark a URL as crawled.
        """
        self.conn.execute("UPDATE pages SET crawled = 1 WHERE url = ?", (url,))
        self.conn.commit() 

    def get_uncrawled_urls(self):
        """
        Get all uncrawled URLs from the database.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT url FROM pages WHERE crawled = 0 ORDER BY depth")
        rows = cur.fetchall()
        return [row[0] for row in rows]

    def get_depth(self, url):
        """
        Get the depth of a given URL.

        :param url: str, the URL to get the depth of
        """
        cur = self.conn.cursor()
        cur.execute("SELECT depth FROM pages WHERE url = ?", (url,))
        row = cur.fetchone()
        return row[0] if row else None
    
    def is_useful_link(self, link, base_url):
        """
        Determine if a link is "useful".
        Conditions for ignoring links:
        - Empty link or None.
        - Links that lead to the same page section (start with '#').
        - Links that are not http(s).
        - Multimedia or non-HTML links.

        :param link: str, the link to check
        :param base_url: str, the base URL
        """
        if not link:
            return False
        parsed = urlparse(link)

        if parsed.fragment and not parsed.path:
            return False

        absolute_link = urljoin(base_url, link)
        parsed_abs = urlparse(absolute_link)
        if parsed_abs.scheme not in ("http", "https"):
            return False

        # Ensure the domain is gatech.edu
        if not parsed_abs.netloc.endswith("gatech.edu"):
            return False

        non_html_exts = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                         '.mp3', '.mp4', '.avi', '.wav', '.zip']
        if any(absolute_link.lower().endswith(ext) for ext in non_html_exts):
            return False

        return True

    def fetch_links(self, url):
        """
        Fetch and parse all useful links from the given URL.

        :param url: str, the URL to fetch links from
        """
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag.get('href')
                    if self.is_useful_link(href, url):
                        absolute_link = urljoin(url, href)
                        links.append(absolute_link)

                return links
            else:
                # Non-200 status, treat as empty
                return []
        except requests.RequestException:
            # In case of timeout, connection error, etc.
            return []

    def crawl(self):
        """
        Perform the crawling based on the current state of the database.
        """
        # Start BFS-like crawl. Initialize queue with uncrawled URLs
        to_crawl = deque(self.get_uncrawled_urls())

        while to_crawl:
            current_url = to_crawl.popleft()
            current_depth = self.get_depth(current_url)
            if current_depth is None:
                continue

            if current_depth >= self.depth:
                continue

            # Check if already crawled
            # Since we always fetch from db, it's possible it got crawled in another iteration
            cur = self.conn.cursor()
            cur.execute("SELECT crawled FROM pages WHERE url = ?", (current_url,))
            row = cur.fetchone()
            if row and row[0] == 1:
                continue

            # Fetch links
            new_links = self.fetch_links(current_url)
            # Insert new unique links
            # The database checks duplicates for us, but we call insert_page anyway
            new_depth = current_depth + 1
            for link in new_links:
                self.insert_page(link, current_url, new_depth)

            # Mark current as crawled
            self.mark_crawled(current_url)

            for link in new_links:
                to_crawl.append(link)


if __name__ == '__main__':
    db_file = 'crawler.db'

    # Initialize the crawler
    crawler = Crawler(url='https://ece.gatech.edu/', db_file=db_file, max_depth=2)
    crawler.crawl()

    # Close the connection
    crawler.conn.close()
    print("Done.")