from pydantic import BaseModel, EmailStr
from typing import Optional


class UserAuthOut(BaseModel):
    id_usuario: int
    nombre: str
    username: str
    id_rol: int
    rol_nombre: Optional[str] = None
    estado: bool


class ResponseLoggin(BaseModel):
    user: UserAuthOut
    access_token: str 

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
