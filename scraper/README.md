# Scraper
## Project Overview
1. Crawler crawls website and builds a map of website directory, stored in a database.
2. Visualiser visualises the map in a visual form xD.
3. Scraper reads the database and scrapes the data.
## Requirements
1. sqlite3
2. networkx
3. scrapy
4. html2text
5. bs4
6. dash
7. pandas
## Run Crawler
scrapy crawl crawler_spider
cntrl-c to shut down (ONLY PRESS IT ONCE FOR CLEAN SHUTDOWN WHICH ALLOWS RESUME FEATURE)
## TODO
1. Fix proxy code.
2. Remove headers and footers when converting to text.
