# 在後端隨便建一個臨時路由，或直接在terminal執行
import sqlite3
conn = sqlite3.connect("alerts.db")
cursor = conn.cursor()

# 看資料庫裡所有資料
cursor.execute("SELECT * FROM alerts")
print(cursor.fetchall())

# 看欄位結構
cursor.execute("PRAGMA table_info(alerts)")
print(cursor.fetchall())