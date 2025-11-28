# scripts/mk_admin_user.py
"""
Gera um usuário admin no banco com senha gerada/definida.
Uso:
python scripts/mk_admin_user.py --email admin@local.test --password SECRET


Ele imprime o id do usuário inserido.
"""
import argparse
import os
import psycopg2
from passlib.hash import argon2


DSN = os.environ.get("DATABASE_URL", "postgresql://dermasync_dev:admin123@localhost:5432/dermasync_dev")


parser = argparse.ArgumentParser()
parser.add_argument('--email', required=True)
parser.add_argument('--password', required=True)
args = parser.parse_args()


pwd_hash = argon2.hash(args.password)


conn = psycopg2.connect(DSN)
cur = conn.cursor()
cur.execute("SELECT id FROM public.users WHERE email=%s", (args.email,))
if cur.fetchone():
    print('User already exists: aborting')
else:
    cur.execute(
        "INSERT INTO public.users (id, email, password_hash, role, is_active) VALUES (gen_random_uuid(), %s, %s, %s, true) RETURNING id;",
        (args.email, pwd_hash, 'admin')
    )
    uid = cur.fetchone()[0]
    conn.commit()
    print('Inserted user id:', uid)
cur.close()
conn.close()