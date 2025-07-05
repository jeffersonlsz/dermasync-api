# app/archlog_sync/parser.py
# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from pathlib import Path

def parse_logs(path: str):
    groups = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        entry = json.loads(line)
        groups[ entry["request_id"] ].append(entry)
    return groups

if __name__ == "__main__":
    import sys
    for req_id, entries in parse_logs(sys.argv[1]).items():
        print(f"{req_id}: {len(entries)} eventos")
