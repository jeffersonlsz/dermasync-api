# app/main.py
# -*- coding: utf-8 -*-
""" Main entry point for the DermaSync API backend.
This module initializes the FastAPI application, sets up middleware for logging requests,
and includes the API routers for different functionalities.
"""

import datetime
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.archlog_sync.middleware import LogRequestMiddleware
from app.archlog_sync.logger import registrar_log
from app.routes import health, imagens, relatos

app = FastAPI(title="DermaSync API - Backend")

app.add_middleware(LogRequestMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.datetime.now(datetime.timezone.utc)
    request_id = uuid4().hex

    # Executa o endpoint
    response = await call_next(request)

    end = datetime.datetime.now(datetime.timezone.utc)
    duration_ms = int((end - start).total_seconds() * 1000)



    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou especifique ["https://www.seusite.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Incluindo o roteador da API
# app.include_router(api_router)


app.include_router(imagens.router)
app.include_router(relatos.router)
app.include_router(health.router)


@app.get("/")
def home():
    return {"mensagem": "API online."}
