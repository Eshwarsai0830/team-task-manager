import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Eshwar#bittu30",
        database="team_task_manager"
    )