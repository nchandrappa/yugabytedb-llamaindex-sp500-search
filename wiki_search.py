from dotenv import load_dotenv
import os
import yfinance as yf
# Load environment variables from .env file
load_dotenv()

def get_env_vars(*args):
    return [os.getenv(arg) for arg in args]

from constants import symbols
import psycopg2
import logging

OPENAI_API_KEY, DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_PORT = get_env_vars('OPENAI_API_KEY', 'DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_PORT')

# Establish database connection
# LOCALDB_URL_STRING = (
# "postgresql+psycopg2://"
# + DB_USERNAME
# + ":"
# + DB_PASSWORD
# + "@"
# + DB_HOST
# + ":"
# + DB_PORT
# + "/"
# + DB_NAME
# )

# connection_string = "postgresql://postgres:password@localhost:5432"
# db_name = "vector_db"
# conn = psycopg2.connect(LOCALDB_URL_STRING)
# conn.autocommit = True

# with conn.cursor() as c:
#     c.execute(f"DROP DATABASE IF EXISTS {db_name}")
#     c.execute(f"CREATE DATABASE {db_name}")

# logging.info("Database created")

import wikipedia
from llama_index.readers.wikipedia import WikipediaReader
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.postgres import PGVectorStore

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

    logging.info("Wiki pages to be loaded: ", len(wiki_pages))
    
    # auto_suggest allows wikipedia to change page search string
    documents = WikipediaReader().load_data(pages=wiki_pages, auto_suggest=False)
    logging.info(f"Wiki pages loaded: ", len(documents))
    
    
    vector_store = PGVectorStore.from_params(
        database=DB_NAME,
        host=DB_HOST,
        password=DB_PASSWORD,
        port=DB_PORT,
        user=DB_USERNAME,
        table_name="snp_wiki_embeddings",
        embed_dim=1536,  # openai embedding dimension
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )

    storage_context_yugabytedb_vs = StorageContext.from_defaults(vector_store=vector_store)
    wiki_vector_index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context_yugabytedb_vs, show_progress=True
    )
    wiki_query_engine = wiki_vector_index.as_query_engine()
    
    logging.info("Created wiki_query_engine for the first time")
else:
    storage_context = StorageContext.from_defaults(persist_dir="wiki_index")
    index = load_index_from_storage(storage_context=storage_context)
    wiki_query_engine = index.as_query_engine()
    print("Loaded wiki_query_engine index from storage")
