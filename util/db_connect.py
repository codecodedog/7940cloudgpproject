import mysql.connector
import os
from util.logger import logger
from dotenv import load_dotenv

load_dotenv()

# Connection details
host = os.getenv('DB_ENDPOINT')
port = 3306
database = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

def get_connection():
    # Establish connection
    conn = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password
    )

    cursor = conn.cursor()
    print("Connection established successfully!")
    return conn
    '''
    # Example query
    cursor.execute("SELECT * FROM user")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
     
    # Close connection
    cursor.close()
    conn.close()
    '''
    
if __name__ == "__main__":
    get_connection()