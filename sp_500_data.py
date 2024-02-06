import pprint
pp = pprint.PrettyPrinter(indent=4)
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

def get_env_vars(*args):
    return [os.getenv(arg) for arg in args]

DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_PORT = get_env_vars('DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_PORT')

import psycopg2
import json
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

import yfinance as yf
from constants import symbols

conn = psycopg2.connect(
    dbname=DB_NAME, 
    user=DB_USERNAME, 
    password=DB_PASSWORD, 
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()
cursor.execute("select exists (select from information_schema.columns where table_name = 'companies')")
table_exists = cursor.fetchone()[0]
print("Does table exist?")
print(table_exists)

column_names_in_db = []
if table_exists == True:
    cursor.execute("select column_name from information_schema.columns where table_name = 'companies'")
    rows = cursor.fetchall()
    # Extract column names from rows and return as a list
    column_names_in_db = [row[0] for row in rows]


print("column names in db:")
print(column_names_in_db)


def switch_on_field_type(type):
    if type == "float":
        return "FLOAT"
    elif type == "int":
        return "BIGINT"
    elif type == "list":
        return "JSONB"
    elif type == "str":
        return "VARCHAR"
    return "OTHER"

def switch_on_value(val):
    val_type = type(val).__name__
    if  val_type == "str":
        # Allows strings with apostrophes to be inserted to DB
       return f"{val}"
    if val_type == "list":
        return f"{json.dumps(val)}"
        # return val
    return val

def switch_on_special_character(key):
    char_type = type(key[0]).__name__

    # if key begins with a number, it needs the be wrapped in double quotes
    if key[0].isdigit():
        return f"\"{key}\""
    
    return key


companies = {}
table_columns = []
table_columns_with_types = []

for i in range(0, len(symbols)):
# for i in range(0, 1):
    company = yf.Ticker(symbols[i])

    info = company.info
    companies[symbols[i]] = info
    keys = list(info.keys())

    for j in range(0, len(keys)):
        if keys[j] not in table_columns:
            table_columns.append(f'{keys[j]}')
            table_columns_with_types.append(f"{switch_on_special_character(keys[j])} {switch_on_field_type(type(info[keys[j]]).__name__)}")

schema = f"CREATE TABLE companies({', '.join(table_columns_with_types)});"

print(schema)

if not table_exists:
    cursor.execute(schema)
    conn.commit()

for j in range(0, len(symbols)):
    print(companies)
    company_info = companies[symbols[j]]
    keys = list(company_info.keys())

    def get_val(key):
        return switch_on_value(company_info[key])
    
    pp.pprint(keys)
    pp.pprint(company_info)

    val_string_segment = '%s,' * (len(keys) - 1) + '%s'

    stringified_keys = map(switch_on_special_character, keys)
    stringified_keys_list = list(stringified_keys)

    insert_statement = f"INSERT INTO companies({', '.join(stringified_keys_list)}) VALUES({val_string_segment})"
    
    statement_values = map(get_val, keys)
    statement_values_list = list(statement_values)

    formatted_list = [(item,) for item in statement_values_list]
    formatted_tuple = tuple(statement_values_list)

    cursor.execute(insert_statement, formatted_tuple)
    conn.commit()


# # Commit the transaction

cursor.close()
conn.close()
