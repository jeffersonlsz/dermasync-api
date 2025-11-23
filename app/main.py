# app/main.py
# -*- coding: utf-8 -*-
"""Main entry point for the DermaSync API backend.
This module initializes the FastAPI application, sets up middleware for logging requests,
and includes the API routers for different functionalities.
"""

import datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.archlog_sync.logger import registrar_log
from app.archlog_sync.middleware import LogRequestMiddleware
from app.routes import auth, health, imagens, relatos

app = FastAPI(title="DermaSync API - Backend")

# TODO: Implementar rate limiting por IP e por usuário.
# Biblioteca recomendada: 'slowapi'
# Exemplo de implementação:
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
#
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(auth.router)


@app.get("/")
def home():
    return {"mensagem": "API online."}
