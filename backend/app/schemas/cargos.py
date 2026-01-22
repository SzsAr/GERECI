from pydantic import BaseModel, Field
from typing import Optional


class CargoCreate(BaseModel):
    """Schema para crear un nuevo cargo"""
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del cargo")
    descripcion: Optional[str] = Field(None, max_length=200, description="Descripción del cargo")
    estado: Optional[int] = Field(1, ge=0, le=1, description="Estado del cargo (0=inactivo, 1=activo)")


class CargoUpdate(BaseModel):
    """Schema para actualizar un cargo existente"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100, description="Nombre del cargo")
    descripcion: Optional[str] = Field(None, max_length=200, description="Descripción del cargo")
    estado: Optional[int] = Field(None, ge=0, le=1, description="Estado del cargo (0=inactivo, 1=activo)")


class CargoOut(BaseModel):
    """Schema de respuesta para cargo"""
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: int

    class Config:
        from_attributes = True
