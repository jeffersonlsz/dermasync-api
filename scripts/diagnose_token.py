# diagnose_token.py
import os, sys
from jose import jwt, JWTError

# cole aqui o token de login que apareceu no teste (login body)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0YzIzYWNjYS0xOThmLTQxODgtOTc1ZC1mZmFhZWNhNTk0NWYiLCJleHAiOjE3NjQxMDY2MjF9.o8SLWuxdGM4AOp360uwGlrzjNFV4QDWH15BEQH_O058"

print("ENV SECRET_KEY:", os.environ.get("SECRET_KEY"))
print("Length SECRET_KEY:", len(os.environ.get("SECRET_KEY") or ""))

try:
    payload = jwt.decode(TOKEN, os.environ.get("SECRET_KEY"), algorithms=["HS256"])
    print("DECODE OK, payload:", payload)
except JWTError as e:
    print("DECODE FAILED:", repr(e))
    sys.exit(1)
