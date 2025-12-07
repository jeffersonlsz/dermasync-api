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
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None


class Token(BaseModel):
    """
    Representa o token de acesso da API (contrato unificado).

    Campos:
      - access_token: token JWT de acesso (curta duração)
      - expires_in_seconds: duração do access token em segundos (tempo de vida)
      - refresh_token: token de refresh (long-lived)
      - refresh_token_expires_in_days: validade do refresh token em dias
      - user: informações públicas do usuário
    """

    access_token: str
    expires_in_seconds: int
    refresh_token: str
    refresh_token_expires_in_days: int
    user: "UserPublicProfile"


class RefreshTokenRequest(BaseModel):
    """
    Corpo da requisição para o endpoint de refresh de token.
    """
    refresh_token: str


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


# Em Pydantic v2, model_rebuild re-resolves forward refs
Token.model_rebuild()
