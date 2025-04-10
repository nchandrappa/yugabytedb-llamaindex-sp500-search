from dotenv import load_dotenv
import os
import yfinance as yf
# Load environment variables from .env file
load_dotenv()

def get_env_vars(*args):
    return [os.getenv(arg) for arg in args]

from constants import symbols

OPENAI_API_KEY, DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_PORT = get_env_vars('OPENAI_API_KEY', 'DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_PORT')

import wikipedia
from llama_index import download_loader
from llama_index import VectorStoreIndex, StorageContext, load_index_from_storage
WikipediaReader = download_loader("WikipediaReader")

PERSIST_DIR = "./wiki_index"
if not os.path.exists(PERSIST_DIR):
    wiki_pages = []
    for i in range(0, len(symbols)):
        print(symbols[i])
        ticker = yf.Ticker(symbols[i])
        try:
            info = ticker.info  # Attempt to fetch the info
        except Exception as e:
            print(f"Error fetching info for {symbols[i]}: {e}")
            continue  # Skip to the next symbol if there's an error

        if 'longName' in ticker.info:
            print(ticker.info["longName"])
            search_results = wikipedia.search(ticker.info["longName"])[0]
            wiki_pages.append(search_results)

    loader = WikipediaReader()
    # auto_suggest allows wikipedia to change page search string
    documents = loader.load_data(pages=wiki_pages, auto_suggest=False)
    print(len(documents))

    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist("wiki_index")
    wiki_query_engine = index.as_query_engine()
    print("Created wiki_query_engine for first time")
else:
    storage_context = StorageContext.from_defaults(persist_dir="wiki_index")
    index = load_index_from_storage(storage_context=storage_context)
    wiki_query_engine = index.as_query_engine()
    print("Loaded wiki_query_engine index from storage")
