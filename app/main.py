# app/main.py
# -*- coding: utf-8 -*-
"""
Main entry point for the DermaSync API backend.
"""

import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Middleware de logging
from app.archlog_sync.middleware import LogRequestMiddleware

# Conexão com o banco
from app.db.connection import Base, engine

# Routers existentes
from app.routes import auth as auth_routes
from app.routes import health
from app.routes import imagens
from app.routes import relatos
from app.routes import me

from app.services.effects.register_effects import register_all_effect_executors





class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_body = None
        try:
            request_body = await request.body()
        except Exception:
            request_body = b"[could not read body]"
        try:
            response = await call_next(request)
            status = response.status_code
            duration = (time.time() - start) * 1000
            logging.info("%s %s %s -> %d (%.1fms) body_len=%d",
                         request.method, request.url.path, request.client.host if request.client else "-",
                         status, duration, len(request_body or b""))
            return response
        except Exception as e:
            duration = (time.time() - start) * 1000
            logging.exception("Unhandled exception for %s %s (%.1fms): %s", request.method, request.url.path, duration, e)
            raise


# ============================================================
# Inicialização do FastAPI
# ============================================================

app = FastAPI(
    title="DermaSync API - Backend",
    version="1.0.0",
    description="Backend moderno do DermaSync com Postgres, SQLAlchemy e autenticação JWT."
)

# ============================================================
# CORS — CONFIGURE AQUI IMEDIATAMENTE (antes de outros middlewares)
# ============================================================
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    # "https://seu-dominio.com"  # produção: coloque aqui
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,        # se usar cookies / Authorization credentials
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============================================================
# Banco de dados — Criar tabelas (apenas ambiente dev)
# ============================================================
Base.metadata.create_all(bind=engine)

# ============================================================
# Middlewares (custom) — depois do CORS
# ============================================================
app.add_middleware(LogRequestMiddleware)
app.add_middleware(LoggingMiddleware)


# ============================================================
# Rotas — incluir routers
# ============================================================
app.include_router(auth_routes.router)
app.include_router(imagens.router)
app.include_router(relatos.router)
app.include_router(health.router)
app.include_router(me.router)

@app.on_event("startup")
async def startup():
    register_all_effect_executors()

# ============================================================
# Endpoints básicos
# ============================================================
@app.get("/")
def home():
    return {"mensagem": "API online."}
