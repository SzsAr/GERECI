from pydantic import BaseModel,  Field
from typing import Optional

class UserBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    id_rol: int
    id_cargo: Optional[int] = Field(default=None, description="ID del cargo del usuario")
    documento: str = Field(min_length=5, max_length=20)
    username: str = Field(min_length=3, max_length=50)
    firma: Optional[str] = Field(default=None, max_length=5000)
    estado: bool

class UserCreate(UserBase):
    pass_hash: str = Field(min_length=8)

class UserUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=80)
    documento: Optional[str] = Field(default=None, min_length=5, max_length=20)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    id_rol: Optional[int] = Field(default=None)
    id_cargo: Optional[int] = Field(default=None)
    firma: Optional[str] = Field(default=None, max_length=5000)
    pass_hash: Optional[str] = Field(default=None, min_length=8)

class UserEstado(BaseModel):
    estado: Optional[bool] = None

class UserOut(UserBase):
    id_usuario: int
    rol_nombre: Optional[str] = None
    cargo_nombre: Optional[str] = None