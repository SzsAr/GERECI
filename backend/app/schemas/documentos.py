"""
Pydantic schemas for documentos
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentoCreate(BaseModel):
    id_tipo: int = Field(..., description="ID del tipo de documento")
    id_plantilla: int = Field(..., description="ID de la plantilla a usar")
    asunto: str = Field(..., min_length=3, max_length=255, description="Asunto del documento")


class DocumentoUpdate(BaseModel):
    id_tipo: Optional[int] = None
    id_plantilla: Optional[int] = None
    asunto: Optional[str] = Field(None, min_length=3, max_length=255)
    ruta_word_generado: Optional[str] = Field(None, max_length=500)
    ruta_pdf_final: Optional[str] = Field(None, max_length=500)
    fecha_emision: Optional[datetime] = None


class DocumentoStateChange(BaseModel):
    nuevo_estado: str = Field(..., description="Nuevo estado del documento")
    descripcion_cambio: Optional[str] = Field(None, description="Motivo del cambio de estado")


class DocumentoOut(BaseModel):
    id: int
    id_tipo: int
    id_plantilla: int
    usuario_genera: int
    asunto: str
    consecutivo: Optional[str]
    fecha_creacion: datetime
    fecha_emision: Optional[datetime]
    ruta_word_generado: Optional[str]
    ruta_pdf_final: Optional[str]
    estado: str
