"""
Pydantic schemas for firmas_digitales
"""
from pydantic import BaseModel, Field
from datetime import datetime


class FirmaDigitalCreate(BaseModel):
    id_usuario: int = Field(..., description="ID del usuario que firma")
    id_documento: int = Field(..., description="ID del documento firmado")


class FirmaDigitalOut(BaseModel):
    id: int
    id_usuario: int
    id_documento: int
    fecha_firma: datetime
