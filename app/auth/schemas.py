"""
Este módulo define os schemas (modelos de dados) para autenticação e usuários.
"""
from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Representa um usuário no sistema interno.
    """

    id: str = Field(..., description='ID interno da aplicação, ex: "usr_a82f91c3"')
    firebase_uid: Optional[str] = Field(None, description="UID vindo do Firebase")
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Literal["admin", "colaborador", "usuario_logado", "anon"] = "usuario_logado"
    is_active: bool = Field(True, description="Se false, bloqueia acesso imediatamente")
    idade_aprox: Optional[int] = Field(None, description="Pode ser usado para personalização do feed")
    principais_areas_pele: Optional[List[str]] = Field(
        None, description='ex ["mãos","pescoço"]'
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPublicProfile(BaseModel):
    """
    Informações públicas do usuário, seguras para retornar ao cliente.
    """

    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None


class SessionRequest(BaseModel):
    firebase_id_token: str


class SessionState(BaseModel):
    authenticated: bool = True
    issued_at: datetime


class SessionResponse(BaseModel):
    user: UserPublicProfile
    session: SessionState
