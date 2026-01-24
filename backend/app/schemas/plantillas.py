"""
Pydantic schemas for plantillas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class PlantillaCreate(BaseModel):
    id_tipo: int
    nombre: str
    nombre_archivo: str
    ruta_almacenamiento: Optional[str] = None
    campos_json: Optional[Dict[str, Any]] = None


class PlantillaUpdate(BaseModel):
    id_tipo: Optional[int] = None
    nombre: Optional[str] = None
    nombre_archivo: Optional[str] = None
    ruta_almacenamiento: Optional[str] = None
    campos_json: Optional[Dict[str, Any]] = None


class PlantillaOut(BaseModel):
    id: int
    id_tipo: int
    nombre: str
    nombre_archivo: str
    ruta_almacenamiento: Optional[str] = None
    campos_json: Optional[Dict[str, Any]] = None
    tipo_nombre: Optional[str] = None
