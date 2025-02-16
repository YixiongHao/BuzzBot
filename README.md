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

## Launch Chainlit App  

Go to the `app` directory and launch the Chainlit app: 

```bash
cd app && chainlit run app.py -w
```

The `-w` flag runs the app in watch mode, which allows you to edit the app and see the changes without restarting the app.

## Pipeline
In project root directory
1. Run Scraper: `scrapy crawl crawler_spider`
2. Run Visualiser: `python -m visualise.visualiser`
3. Download Files: `python -m downloader.main`
4. Run Processor: `python -m processor.processor`

## Config Import
```
import os
import importlib.util

root = f"{os.path.dirname(os.path.abspath(__file__))}/.."  # The Root Directory
spec = importlib.util.spec_from_file_location("CONFIG", f"{root}/CONFIG.py")  # Module
CONFIG = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CONFIG)
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
