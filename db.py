import mysql.connector
import os
from urllib.parse import urlparse

def get_db_connection():
    url = os.getenv("DATABASE_URL")

    parsed = urlparse(url)

    return mysql.connector.connect(
        host=parsed.hostname,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip('/'),
        port=parsed.port
    )