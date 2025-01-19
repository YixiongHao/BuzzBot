# Scraper
## Project Overview
1. Crawler crawls the website and stores it as a NDJSON file.
2. Visualiser creates a map of the crawled webpages.
3. Proxy is a proxy finder.
4. Downloader reads the NDJSON file and downloads it.
## Requirements
1. sqlite3
2. networkx
3. scrapy
4. html2text
5. bs4
6. dash
7. pandas
## Run Crawler
`scrapy crawl crawler_spider`
## Stop Cralwer
`cntrl-c` 
- (Only press it once for a clean shutdown, allowing the "resume" feature to work.)
## TODO
1. Fix proxy code.
2. Remove headers and footers when converting to text.
