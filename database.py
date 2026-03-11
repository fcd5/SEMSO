import sqlite3

conn = sqlite3.connect("alerts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet TEXT,
    coin TEXT,
    target_price REAL,
    alert_type TEXT,
    email TEXT,
    triggered INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()