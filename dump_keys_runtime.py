# dump_keys_runtime.py
import importlib
from pprint import pprint

# imports dinâmicos (forçam carregamento dos módulos)
sec = importlib.import_module("app.auth.security")
dep = importlib.import_module("app.auth.dependencies")
cfg = None
try:
    cfg = importlib.import_module("app.config")
except Exception:
    cfg = None

print("app.auth.security.SECRET_KEY:", getattr(sec, "SECRET_KEY", None))
print("app.auth.security.ALGORITHM:", getattr(sec, "ALGORITHM", None))
print("app.auth.dependencies.SECRET_KEY:", getattr(dep, "SECRET_KEY", None))
if cfg:
    print("app.config (if exists) attributes:")
    pprint({k: getattr(cfg, k) for k in dir(cfg) if k.isupper()})
else:
    print("app.config not found or failed to import.")
