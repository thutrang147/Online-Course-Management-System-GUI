import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def create_connection():
    """Create a database connection using configuration from config.py."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    return None


# import mysql.connector
# from mysql.connector import Error
# from dotenv import load_dotenv
# import os

# load_dotenv()  # Load variables from .env

# def create_connection():
#     """Create a database connection using configuration from config.py."""
#     try:
#         connection = mysql.connector.connect(
#             host=os.getenv('DB_HOST'),
#             database=os.getenv('DB_NAME'),
#             user=os.getenv('DB_USER'),
#             password=os.getenv('DB_PASSWORD')
#         )
#         if connection.is_connected():
#             return connection
#     except Error as e:
#         print(f"Error connecting to MySQL: {e}")
#         return None
#     return None