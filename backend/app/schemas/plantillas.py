"""
Pydantic schemas for plantillas - gestión de tablas dinámicas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class PlantillaCreate(BaseModel):
    """Schema para crear una plantilla"""
    id_tipo: int = Field(..., description="ID del tipo de documento")
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la plantilla (será el nombre de la tabla dinámica)")
    campos_json: Dict[str, str] = Field(..., description="Campos de la plantilla: {'nombre_campo': 'tipo_dato', ...}")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción de la plantilla")

    @field_validator('campos_json')
    @classmethod
    def validar_campos(cls, v: dict):
        allowed = {'varchar','text','int','float','date','datetime','decimal','boolean'}
        reserved = {'id','id_plantilla','id_documento','campos_json','fecha','consecutivo','fecha_creacion'}
        if not isinstance(v, dict) or len(v) == 0:
            raise ValueError('Debe proporcionar al menos un campo')
        for k, t in v.items():
            if not isinstance(k, str) or not k.strip():
                raise ValueError('Nombre de campo inválido')
            key = k.strip().lower().replace(' ', '_')
            if key in reserved:
                raise ValueError(f"El nombre de campo '{k}' está reservado")
            if not isinstance(t, str) or t.lower() not in allowed:
                raise ValueError(f"Tipo de dato inválido para '{k}'")
        return v


class PlantillaUpdate(BaseModel):
    """Schema para actualizar una plantilla"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=255)
    estado: Optional[int] = Field(None, ge=0, le=1)


class PlantillaOut(BaseModel):
    """Schema de respuesta para plantilla"""
    id: int
    id_tipo: int
    nombre: str
    campos_json: Optional[Dict[str, Any]] = None
    descripcion: Optional[str] = None
    estado: int
    fecha_creacion: datetime
    tipo_nombre: Optional[str] = None
    nombre_tabla: Optional[str] = None
    nombre_archivo: Optional[str] = None
    ruta_almacenamiento: Optional[str] = None
    
    model_config = {"from_attributes": True}

