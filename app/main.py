# app/main.py
# -*- coding: utf-8 -*-
"""
Main entry point for the DermaSync API backend.
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.archlog_sync.middleware import LogRequestMiddleware
from app.routes import auth as auth_routes
from app.routes import galeria
from app.routes import galeria_leitura
from app.routes import health
from app.routes import imagens
from app.routes import me
from app.routes import relatos
from app.routes import feed as feed_router
from app.routes.dev_effects import router as dev_effects_router
from app.routes.dev_enrich import router as dev_enrich_router
from app.routes.relato_progress_stream import router as relato_progress_stream_router
from app.routes.relatos_progress import router as relatos_progress_router
from app.services.effects.register_effects import register_all_effect_executors


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all_effect_executors()
    yield


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_body = b""
        try:
            request_body = await request.body()
        except Exception:
            request_body = b"[could not read body]"

        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000
            logging.info(
                "%s %s %s -> %d (%.1fms) body_len=%d",
                request.method,
                request.url.path,
                request.client.host if request.client else "-",
                response.status_code,
                duration,
                len(request_body),
            )
            return response
        except Exception as exc:
            duration = (time.time() - start) * 1000
            logging.exception(
                "Unhandled exception for %s %s (%.1fms): %s",
                request.method,
                request.url.path,
                duration,
                exc,
            )
            raise


app = FastAPI(
    title="DermaSync API - Backend",
    version="1.0.0",
    description="Backend do DermaSync com Firebase Auth, Firestore e FastAPI.",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(LogRequestMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(auth_routes.router)
app.include_router(imagens.router)
app.include_router(relatos.router, prefix="/relatos")
app.include_router(galeria.router)
app.include_router(me.router)
app.include_router(relatos_progress_router)
app.include_router(relato_progress_stream_router)
app.include_router(feed_router.router)
app.include_router(galeria_leitura.router)

if os.getenv("ENVIRONMENT") == "development":
    app.include_router(dev_effects_router)
    app.include_router(dev_enrich_router)
    app.include_router(health.router)


@app.get("/")
def home():
    return {"mensagem": "API online."}
