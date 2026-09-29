
import sqlite3
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
for table in cur.fetchall():
    if 'purchase' in table[0].lower():
        print(table[0])
        cur.execute(f"PRAGMA table_info({table[0]})")
        for col in cur.fetchall():
            print('  ', col[1])

