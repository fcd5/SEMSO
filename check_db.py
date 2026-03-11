import sqlite3

conn = sqlite3.connect("alerts.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(alerts)")
columns = cursor.fetchall()
print(columns)

conn.close()