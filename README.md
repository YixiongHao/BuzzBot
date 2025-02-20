## BuzzBot

This is a simple chatbot app that answers all things related to Georgia Tech, everything from housing, registration, to meal plans.  It indexes all .gatech.edu domains
- Semantic search on sites by name and content
- Time-ranged search on pages by update date
- Question answering about the contents of a webpage
- Support for image/audio content coming soon!

This will be hosted at XXX when ready!

## Virtual Environment

Install necessary packages: 

```bash
pip install -r requirements.txt
conda install anaconda::ffmpeg #for whisper, need the executable
```

## Index Setup
Use the processor to process a folder of files and index them in Elasticsearch: `python processor/processor.py`. You only need to run this once each time the directory is updated.

## Setup OpenAI API Key

Create a `.env` file in the `app` directory with your OpenAI API key:   

```
OPENAI_API_KEY=sk-...
```

## Pipeline
In project root directory
1. Run Scraper: `scrapy crawl crawler_spider`
2. Run Visualiser: `python visualise/visualiser.py`
3. Download Files: `python downloader/main.py`
4. Run Processor: `python processor/processor.py`
5. Run Chainlit: `cd app && chainlit run app.py -w`

The `-w` flag runs the app in watch mode, which allows you to edit the app and see the changes without restarting the app.
## Config Import
```
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import CONFIG
```

## Scraper README
### Project Overview
1. Crawler crawls the website and stores it as a NDJSON file.
2. Visualiser creates a map of the crawled webpages.
3. Proxy is a proxy finder.
4. Downloader reads the NDJSON file and downloads it.
### Requirements
1. sqlite3
2. networkx
3. scrapy
4. html2text
5. bs4
6. dash
7. pandas
### Stop Cralwer
`cntrl-c` 
- (Only press it once for a clean shutdown, allowing the "resume" feature to work.)
### TODO
1. Fix proxy code.
2. Remove headers and footers when converting to text.

### Things
```
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.10.0
```
```
docker run -d --name elasticsearch \
  -p 9200:9200 -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.10.0

```
```
docker start elasticsearch
```