from util.db_connect import get_connection as db

sql = """
ALTER TABLE user
AUTO_INCREMENT = 3;
"""

# Establish database connection
connection = db()
cursor = connection.cursor()

# Execute the SQL statement
cursor.execute(sql)
connection.commit()
print("Table altered successfully")