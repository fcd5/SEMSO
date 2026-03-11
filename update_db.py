import sqlite3

conn = sqlite3.connect("alerts.db")
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE alerts
    ADD COLUMN triggered_at TIMESTAMP DEFAULT NULL
""")

conn.commit()
conn.close()

print("alerts table 已新增 triggered_at 欄位")