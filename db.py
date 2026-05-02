import os
import mysql.connector
from urllib.parse import urlparse

def get_db_connection():
    try:
        url = os.getenv("DATABASE_URL")

        if not url:
            print("DATABASE_URL missing ❌")
            return None

        parsed = urlparse(url)

        return mysql.connector.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            port=parsed.port
        )

    except Exception as e:
        print("DB ERROR:", e)
        return None