# test_db.py
import os, sys
try:
    import psycopg2
except Exception as e:
    print("Instale psycopg2: pip install psycopg2-binary")
    raise SystemExit(1)

url = os.environ.get("DATABASE_URL", "postgresql://dev:devpass@localhost:5432/dermasync_dev")
print("DATABASE_URL =", url)
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("OK:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("ERROR:", e)
    sys.exit(1)
