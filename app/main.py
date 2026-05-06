# app/main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import sys
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# 1. Carregar env vars IMEDIATAMENTE no entrypoint
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    ALLOWED_ORIGINS, ENVIRONMENT
)

from app.application.effects.register_effects import register_all_effect_executors


# Import de rotas (agora seguro, pois o env j est carregado)
from app.routes import (
    auth, galeria, galeria_leitura, health, 
    imagens, relatos, feed, 
    relatos_progress,
    dev_effects, dev_enrich
)
from app.infra.firebase_app import init_firebase

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializao explcita e controlada
    logging.info(f"DermaSync API iniciando em: {ENVIRONMENT}")
    
    # Centralização da inicialização do Firebase
    init_firebase()
    
    # Registrar executores de efeitos
    register_all_effect_executors()
    
    yield
    logging.info("DermaSync API encerrando.")

app = FastAPI(
    title="DermaSync API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if ENVIRONMENT == "development" else None,
)

# CORS Centralizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de Observabilidade (Seguro: NÃO l o body do request)
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start_time) * 1000
    
    logging.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)"
    )
    return response

# Roteamento
app.include_router(auth.router)
app.include_router(imagens.router)
app.include_router(relatos.router, prefix="/relatos")
app.include_router(galeria.router)
app.include_router(relatos_progress.router)
app.include_router(feed.router)
app.include_router(galeria_leitura.router)
app.include_router(health.router)

if ENVIRONMENT in ["development", "testing"]:
    app.include_router(dev_effects.router)
    app.include_router(dev_enrich.router)

@app.get("/")
async def root():
    return {"status": "online", "service": "DermaSync API"}
