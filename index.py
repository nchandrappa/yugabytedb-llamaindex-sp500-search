from sqlalchemy import (
    create_engine
)

# Logs additional information, including runtime information regarding LlamaIndex
# import logging
# import sys
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


from llama_index import SQLDatabase, ServiceContext
from llama_index.llms import OpenAI

from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv(dotenv_path="./.env")

# helper function to destructure environment variables
def get_env_vars(*args):
    return [os.getenv(arg) for arg in args]

OPENAI_API_KEY, DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_PORT = get_env_vars('OPENAI_API_KEY', 'DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_PORT')

# import psycopg2
# import json

# Establish database connection
LOCALDB_URL_STRING = (
"postgresql+psycopg2://"
+ DB_USERNAME
+ ":"
+ DB_PASSWORD
+ "@"
+ DB_HOST
+ ":"
+ DB_PORT
+ "/"
+ DB_NAME
)

from llama_index.query_engine import SQLJoinQueryEngine
from llama_index.tools.query_engine import QueryEngineTool
from llama_index.indices.struct_store.sql_query import NLSQLTableQueryEngine
from llama_index import Prompt

template = (
    "We have provided the context information below. \n"
    "---------------------\n"
    "{context_str}"
    "\n-------------------\n"
    "Given this information, please answer the following question: {query_str}"
)


qa_template = Prompt(template)

sql_engine = create_engine(f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
chunk_size = 1024
llm = OpenAI(temperature=0.1, model="gpt-4", streaming=True)
service_context = ServiceContext.from_defaults(chunk_size=chunk_size, llm=llm)
sql_database = SQLDatabase(sql_engine, include_tables=["companies"])
table_details = {
    "companies": "contains financial information and metadata for S&P 500 companies",
}

from llama_index.indices.struct_store.sql_query import NLSQLTableQueryEngine

sql_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    tables=["companies"],
)

from wiki_search import wiki_query_engine

sql_tool = QueryEngineTool.from_defaults(
    query_engine=sql_engine,
    description=(
        "Useful for translating a natural language query into a SQL query over"
        " a table containing: companies, containing stats about S&P 500 companies."
    ),
)
s_engine_tool = QueryEngineTool.from_defaults(
    query_engine=wiki_query_engine,
    description=(
        f"Useful for answering qualitative questions about different S&P 500 companies."
    ),
)

query_engine = SQLJoinQueryEngine(
    sql_tool, s_engine_tool, service_context=service_context
)

query_str = input("What is your question? \n\n")

while query_str != "":
    augmented_query_string = f"Answer this question specifically: {query_str}. Ignore null values."
    response = query_engine.query(augmented_query_string)
    print(response)
    query_str = input("What is your question? \n\n")