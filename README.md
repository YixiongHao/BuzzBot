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
