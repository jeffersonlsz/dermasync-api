# app/archlog_sync/parser.py
# -*- coding: utf-8 -*-
import json
import sys
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_logs(path: str):
    logger.info(f"Parsing logs from: {path}")
    """ Parse a JSONL log file and group entries by the 'caller' field.
    Each line in the file is expected to be a JSON object with a 'caller' key.
    Returns a dictionary where keys are caller names and values are lists of log entries.
    """
    groups = defaultdict(list)
    
    if not Path(path).exists():
        logger.error(f"Log file not found: {path}")
        raise FileNotFoundError(f"Log file not found: {path}")
    


    for line in Path(path).read_text().splitlines():
        entry = json.loads(line)
        logger.info(f"Processing entry: {entry}")
        groups[entry["request_id"]].append(entry)
    
    return groups


if __name__ == "__main__":

    for req_id, entries in parse_logs(sys.argv[1]).items():
        print(f"{req_id}: {len(entries)} eventos")
