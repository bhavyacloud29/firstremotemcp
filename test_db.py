from connection import get_connection
import pyodbc
from db_init import create_database_if_not_exists,create_tables_if_not_exists
print(pyodbc.drivers())


create_database_if_not_exists()
create_tables_if_not_exists()
print("Everything works")
conn = get_connection()

cursor = conn.cursor()

cursor.execute("SELECT @@VERSION")

print(cursor.fetchone()[0])

conn.close()