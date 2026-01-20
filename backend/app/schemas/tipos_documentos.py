"""
Pydantic schemas for tipos_documentos
"""
from pydantic import BaseModel


class TipoDocumentoCreate(BaseModel):
    nombre: str
    codigo: str
    requiere_juridica: bool = False


class TipoDocumentoUpdate(BaseModel):
    nombre: str = None
    codigo: str = None
    requiere_juridica: bool = None


class TipoDocumentoOut(BaseModel):
    id: int
    nombre: str
    codigo: str
    requiere_juridica: bool
