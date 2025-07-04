import json
from datetime import datetime
from .schemas import LogEntry

def registrar_log(log_path: str, **kwargs):
    entry = LogEntry(timestamp=datetime.utcnow(), **kwargs)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry.json() + "\\n")