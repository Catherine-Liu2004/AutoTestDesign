import sqlite3, os
db_path = 'autotestdesign.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print('Tables:', tables)
    for t in tables:
        cols = conn.execute(f"PRAGMA table_info({t[0]})").fetchall()
        print(f'{t[0]}:', [c[1] for c in cols])
    conn.close()
else:
    print('No DB yet')
