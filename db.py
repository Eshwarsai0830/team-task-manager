import psycopg2
import os

def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        print("DB Connection Error:", e)
        return None