import psycopg2
import os
from urllib.parse import urlparse

def get_db_connection():
    try:
        db_url = os.environ.get("DATABASE_URL")

        if not db_url:
            print("❌ DATABASE_URL not found")
            return None

        result = urlparse(db_url)

        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )

        print("✅ Database connected")
        return conn

    except Exception as e:
        print(f"❌ DB connection error: {e}")
        return None