"""
Definição de modelos de dados (schemas) para Autenticação e Usuários.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """
    Papéis de acesso permitidos no sistema.
    """
    ADMIN = "admin"
    COLABORADOR = "colaborador"
    USUARIO_LOGADO = "usuario_logado"


class User(BaseModel):
    """
    Modelo completo do usuário no banco interno.
    """
    id: str = Field(..., description="ID único interno (usr_...)")
    firebase_uid: str = Field(..., description="UID vinculado ao Firebase Auth")
    email: Optional[str] = Field(None, description="Endereço de e-mail principal")
    display_name: Optional[str] = Field(None, description="Nome de exibição")
    avatar_url: Optional[str] = Field(None, description="URL da foto de perfil")
    role: UserRole = Field(UserRole.USUARIO_LOGADO, description="Nível de acesso")
    is_active: bool = Field(True, description="Define se o usuário tem acesso ao sistema")
    
    # Metadados de perfil
    idade_aprox: Optional[int] = Field(None, description="Idade aproximada para personalização")
    principais_areas_pele: List[str] = Field(
        default_factory=list, 
        description="Lista de áreas da pele de maior interesse"
    )
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPublicProfile(BaseModel):
    """
    Perfil público seguro para retorno em endpoints de sessão e listagem.
    """
    user_id: str = Field(..., description="ID único interno")
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = Field(..., description="Papel do usuário no sistema")


class SessionRequest(BaseModel):
    """
    Solicitação de abertura de sessão via Firebase Token.
    """
    firebase_id_token: str


class SessionState(BaseModel):
    """
    Estado temporal da sessão.
    """
    authenticated: bool = True
    issued_at: datetime


class SessionResponse(BaseModel):
    """
    Resposta padrão após criação de sessão bem-sucedida.
    """
    user: UserPublicProfile
    session: SessionState
