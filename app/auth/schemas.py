"""
DefiniÃ§Ã£o de modelos de dados (schemas) para AutenticaÃ§Ã£o e UsuÃ¡rios.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """
    PapÃ©is de acesso permitidos no sistema.
    """
    ADMIN = "admin"
    COLABORADOR = "colaborador"
    USUARIO_LOGADO = "usuario_logado"


class User(BaseModel):
    """
    Modelo completo do usuÃ¡rio no banco interno.
    """
    id: str = Field(..., description="ID Ãºnico interno (usr_...)")
    firebase_uid: str = Field(..., description="UID vinculado ao Firebase Auth")
    email: Optional[str] = Field(None, description="EndereÃ§o de e-mail principal")
    display_name: Optional[str] = Field(None, description="Nome de exibiÃ§Ã£o")
    avatar_url: Optional[str] = Field(None, description="URL da foto de perfil")
    role: UserRole = Field(UserRole.USUARIO_LOGADO, description="NÃ­vel de acesso")
    is_active: bool = Field(True, description="Define se o usuÃ¡rio tem acesso ao sistema")
    
    # Metadados de perfil
    idade_aprox: Optional[int] = Field(None, description="Idade aproximada para personalizaÃ§Ã£o")
    principais_areas_pele: List[str] = Field(
        default_factory=list, 
        description="Lista de Ã¡reas da pele de maior interesse"
    )
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPublicProfile(BaseModel):
    """
    Perfil pÃºblico seguro para retorno em endpoints de sessÃ£o e listagem.
    """
    user_id: str = Field(..., description="ID Ãºnico interno")
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole = Field(..., description="Papel do usuÃ¡rio no sistema")


class SessionRequest(BaseModel):
    """
    SolicitaÃ§Ã£o de abertura de sessÃ£o via Firebase Token.
    """
    firebase_id_token: str


class SessionState(BaseModel):
    """
    Estado temporal da sessÃ£o.
    """
    authenticated: bool = True
    issued_at: datetime


class SessionResponse(BaseModel):
    """
    Resposta padrÃ£o apÃ³s criaÃ§Ã£o de sessÃ£o bem-sucedida.
    """
    user: UserPublicProfile
    session: SessionState
