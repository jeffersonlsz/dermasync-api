from pydantic import BaseModel

class AuthUser(BaseModel):
    uid: str
    email: str
    role: str  # Ex: 'anonimo', 'usuario_logado', 'admin'