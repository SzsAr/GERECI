from pydantic import BaseModel, Field
from typing import Optional


class RolCreate(BaseModel):
    """Schema para crear un nuevo rol"""
    nombre: str = Field(..., min_length=3, max_length=30, description="Nombre del rol")
    estado: Optional[int] = Field(1, ge=0, le=1, description="Estado del rol (0=inactivo, 1=activo)")


class RolUpdate(BaseModel):
    """Schema para actualizar un rol existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=30, description="Nombre del rol")
    estado: Optional[int] = Field(None, ge=0, le=1, description="Estado del rol (0=inactivo, 1=activo)")


class RolOut(BaseModel):
    """Schema de respuesta para rol"""
    id: int
    nombre: str
    estado: int

    class Config:
        from_attributes = True
