import mysql.connector
import os

# Connection details
host = os.environ['server']
port = 3306
database = os.environ['database']
username = os.environ['username']
password = os.environ['password']

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