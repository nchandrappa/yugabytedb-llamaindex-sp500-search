import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

from llama_index import StorageContext, load_index_from_storage
storage_context = StorageContext.from_defaults(persist_dir="wiki_index")


index = load_index_from_storage(storage_context=storage_context)
wiki_query_engine = index.as_query_engine()

query = input("What would you like to query from the Wikipedia Index")
while query != '':
    print(wiki_query_engine.query(query))
    query = input("What would you like to query from the Wikipedia Index")
