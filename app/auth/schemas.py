"""
Definio de modelos de dados (schemas) para Autenticao e Usurios.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """
    Papis de acesso permitidos no sistema.
    """
    ADMIN = "admin"
    COLABORADOR = "colaborador"
    USUARIO_LOGADO = "usuario_logado"


class User(BaseModel):
    """
    Modelo completo do usurio no banco interno.
    """
    id: str = Field(..., description="ID nico interno (usr_...)")
    firebase_uid: str = Field(..., description="UID vinculado ao Firebase Auth")
    email: Optional[str] = Field(None, description="Endereo de e-mail principal")
    display_name: Optional[str] = Field(None, description="Nome de exibio")
    avatar_url: Optional[str] = Field(None, description="URL da foto de perfil")
    role: UserRole = Field(UserRole.USUARIO_LOGADO, description="Nvel de acesso")
    is_active: bool = Field(True, description="Define se o usurio tem acesso ao sistema")
    
    # Metadados de perfil
    idade_aprox: Optional[int] = Field(None, description="Idade aproximada para personalizao")
    principais_areas_pele: List[str] = Field(
        default_factory=list, 
        description="Lista de reas da pele de maior interesse"
    )
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPublicProfile(BaseModel):
    """
    Perfil pblico seguro para retorno em endpoints de sesso e listagem.
    """
    user_id: str = Field(..., description="ID nico interno")
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = Field(..., description="Papel do usurio no sistema")


class SessionRequest(BaseModel):
    """
    Solicitao de abertura de sesso via Firebase Token.
    """
    firebase_id_token: str


class SessionState(BaseModel):
    """
    Estado temporal da sesso.
    """
    authenticated: bool = True
    issued_at: datetime


class SessionResponse(BaseModel):
    """
    Resposta padro aps criao de sesso bem-sucedida.
    """
    user: UserPublicProfile
    session: SessionState
