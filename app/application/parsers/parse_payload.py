# app/application/parsers/parse_payload.py
import json
from fastapi import HTTPException, status
from app.schema.relato_draft import RelatoDraftInput

def parse_payload_json(payload: str) -> RelatoDraftInput:
    try:
        data = json.loads(payload)
        return RelatoDraftInput(**data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
