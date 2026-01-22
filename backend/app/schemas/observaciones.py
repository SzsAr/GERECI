"""
Pydantic schemas for observaciones
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ObservacionCreate(BaseModel):
    id_documento: int = Field(..., description="ID del documento asociado")
    id_usuario: int = Field(..., description="ID del usuario que observa")
    tipo: str = Field(..., description="JURIDICA o GERENCIA")
    descripcion: str = Field(..., min_length=10, max_length=5000, description="Descripción de la observación")


class ObservacionUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=10, max_length=5000)


class ObservacionOut(BaseModel):
    id: int
    id_documento: int
    id_usuario: int
    fecha: datetime
    tipo: str
    descripcion: str
