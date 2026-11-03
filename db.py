
import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Suru2006",
        database="healthcare_db"
    )

    return connection
