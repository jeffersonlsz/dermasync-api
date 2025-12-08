# app/main.py
# -*- coding: utf-8 -*-
"""
Main entry point for the DermaSync API backend.

- Inicializa a aplicação FastAPI
- Integra SQLAlchemy + Postgres
- Configura middlewares de logging
- Configura CORS
- Inclui rotas de autenticação, saúde, imagens e relatos
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Middleware de logging
from app.archlog_sync.middleware import LogRequestMiddleware

# Conexão com o banco
from app.db.connection import Base, engine

# Routers existentes
from app.routes import auth as auth_routes
from app.routes import health
from app.routes import imagens
from app.routes import relatos

# Router novo da autenticação (JWT)
#from app.auth.router import router as auth_v2_router

from app.routes import me


# ============================================================
# Inicialização do FastAPI
# ============================================================

app = FastAPI(
    title="DermaSync API - Backend",
    version="1.0.0",
    description="Backend moderno do DermaSync com Postgres, SQLAlchemy e autenticação JWT."
)


# ============================================================
# Banco de dados — Criar tabelas (apenas ambiente dev)
# ============================================================

# Em ambiente real, usar Alembic!
Base.metadata.create_all(bind=engine)


# ============================================================
# Middlewares
# ============================================================

# Logging (arquitetura ArchLog)
app.add_middleware(LogRequestMiddleware)

# CORS — liberar frontend durante dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Ajuste para produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Rotas — incluir routers
# ============================================================

# 🔐 Autenticação NOVA (JWT + SQLAlchemy + Postgres)
#app.include_router(auth_v2_router)

# Rotas antigas/mantidas:
app.include_router(auth_routes.router)   # Se quiser remover depois, é só apagar esta linha
app.include_router(imagens.router)
app.include_router(relatos.router)
app.include_router(health.router)
app.include_router(me.router)

# ============================================================
# Endpoints básicos
# ============================================================

@app.get("/")
def home():
    return {"mensagem": "API online."}
