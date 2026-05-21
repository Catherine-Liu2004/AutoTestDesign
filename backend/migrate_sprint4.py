"""One-shot migration: add state_diagram to requirements, ai_oracle to test_cases."""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'autotestdesign.db')
if not os.path.exists(db_path):
    print("DB not found — will be created fresh on first startup.")
else:
    conn = sqlite3.connect(db_path)
    req_cols = [c[1] for c in conn.execute("PRAGMA table_info(requirements)").fetchall()]
    tc_cols  = [c[1] for c in conn.execute("PRAGMA table_info(test_cases)").fetchall()]

    if 'state_diagram' not in req_cols:
        conn.execute("ALTER TABLE requirements ADD COLUMN state_diagram TEXT")
        print("Added requirements.state_diagram")
    else:
        print("requirements.state_diagram already exists")

    if 'ai_oracle' not in tc_cols:
        conn.execute("ALTER TABLE test_cases ADD COLUMN ai_oracle TEXT")
        print("Added test_cases.ai_oracle")
    else:
        print("test_cases.ai_oracle already exists")

    conn.commit()
    conn.close()
    print("Migration complete.")
