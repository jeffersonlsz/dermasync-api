# app/auth/schemas.py
"""
Este módulo define os schemas (modelos de dados) para autenticação e usuários.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Representa um usuário no sistema interno.
    """

    id: str = Field(..., description="ID interno da aplicação, ex: \"usr_a82f91c3\"")
    firebase_uid: str = Field(..., description="UID vindo do Firebase")
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    role: Literal["admin", "colaborador", "usuario_logado", "anon"]
    is_active: bool = Field(
        ..., description="Se false, bloqueia acesso imediatamente"
    )
    idade_aprox: Optional[int] = Field(
        None, description="Pode ser usado para personalização do feed"
    )
    principais_areas_pele: Optional[List[str]] = Field(
        None, description='ex ["mãos","pescoço"]'
    )
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    """
    Representa o token de acesso da API.
    """

    api_token: str
    expires_in_seconds: int
    refresh_token: str
    refresh_token_expires_in_days: int
    user: "UserPublicProfile"


class RefreshTokenRequest(BaseModel):
    """
    Corpo da requisição para o endpoint de refresh de token.
    """
    refresh_token: str



class UserPublicProfile(BaseModel):
    """
    Informações públicas do usuário, seguras para retornar ao cliente.
    """

    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    role: str


class ExternalLoginRequest(BaseModel):
    """
    Corpo da requisição para o endpoint de login externo.
    """

    provider_token: str


class CurrentUser(BaseModel):
    """
    Objeto simplificado representando o usuário atual, para ser usado em dependências.
    """

    user_id: str
    role: str
    is_active: bool

# O Pydantic v2 lida com referências de tipo forward automaticamente.
# Se estivesse no Pydantic v1, precisaria de UserPublicProfile.update_forward_refs(User=User)
Token.model_rebuild() # No Pydantic v2, model_rebuild() é o substituto para update_forward_refs