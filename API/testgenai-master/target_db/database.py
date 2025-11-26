import os
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from self_db import create_execution
from config import settings
import time
from dotenv import load_dotenv
import json
from datetime import date, datetime
from decimal import Decimal
from json import JSONEncoder

# Custom JSON Encoder
class DecimalEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            formatted_decimal = "{:.2f}".format(obj)
            return formatted_decimal
        if isinstance(obj, (datetime, date)):            
            return obj.isoformat()
        return JSONEncoder.default(self, obj)

load_dotenv(override=True) 

# engine = create_engine(settings.target_database_url)

engine = create_engine(
    settings.target_database_url,
    echo=False,
    connect_args={
        "autocommit": False,
        "connect_timeout": 30,
    },
    pool_pre_ping=True,
    pool_size=25,
    pool_recycle=3600,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

"""
IMPORTANT - ENSURE the user is able to perform only limited actions 
Should NOT include DELETE, UPDATE and such permissions
For this version ONLY ALLOW SELECT FROM LIMITED TABLES
"""
def execute_query(query, query_from_llm=False): 
    try:
        session = SessionLocal()
        result = session.execute(query)
        if query_from_llm:
            return [dict(row) for row in result]
        else:
            return [tuple(row) for row in result]
    except Exception as ex:
        print("Error while executing the query:", ex)
    finally:
        session.close()


def execute_query_original(question_id, question_type, usage_type, sql_query, query_from_llm = False, attempt_number = 1):
    start_time = time.time()
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PW")
    db_host = os.environ.get("DB_HOST")
    db_name = os.environ.get("DB_NAME")

    driver = '{ODBC Driver 17 for SQL Server}'  # Adjust driver version if needed

    connection_string = f'DRIVER={driver};SERVER={db_host};DATABASE={db_name};UID={db_user};PWD={db_password}'
    try:
        with pyodbc.connect(connection_string) as conn:
            print("Connected to SQL Server database successfully!")

            # Log the SQL query for debugging
            if attempt_number > 1:
                print(f"Executing SQL (Attempt {attempt_number}):\n{sql_query[:500]}...")

            cursor = conn.cursor()
            cursor.execute(sql_query)
            column_names = [column[0] for column in cursor.description]

            # Fetch the result
            rows = cursor.fetchall()   
            if query_from_llm is False:
               return rows, column_names, None
            else:           
                # Convert rows to list of dictionaries
                result = [dict(zip(column_names, row)) for row in rows]  
                resultset_rows_count = len(result)
                # Serialize to JSON using the custom encoder
                json_result = json.dumps(result, cls=DecimalEncoder, indent=4)               
                time_taken = time.time() - start_time                
                create_execution(usage_type, question_id, question_type, sql_query, json_result, None, attempt_number, time_taken, resultset_rows_count)
                return result, column_names, None
    except pyodbc.Error as ex:
        error_message = str(ex)        
        print("Connection error:", ex)
        time_taken = time.time() - start_time                
        if query_from_llm is True:
            create_execution(usage_type, question_id, question_type, sql_query, None, error_message, attempt_number, time_taken, 0)
        return None, None, f"ran into error {error_message} "
        



