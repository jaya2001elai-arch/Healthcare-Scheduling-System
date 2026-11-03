
from db import get_db_connection
from werkzeug.security import generate_password_hash
import getpass

print("===== CREATE ADMIN ACCOUNT =====")

name = input("Enter Admin Name: ")
email = input("Enter Admin Email: ")
password = getpass.getpass("Enter Admin Password: ")

connection = None
cursor = None

try:
    connection = get_db_connection()
    cursor = connection.cursor()

    hashed_password = generate_password_hash(password)

    query = """
        INSERT INTO users
        (full_name, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """

    values = (name, email, hashed_password, "Admin")

    cursor.execute(query, values)
    connection.commit()

    print("\nAdmin Account Created Successfully!")

except Exception as e:
    print("\nError:", e)

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()
