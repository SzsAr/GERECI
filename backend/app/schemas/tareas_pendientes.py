"""
Pydantic schemas for tareas_pendientes
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TareaPendienteCreate(BaseModel):
    id_documento: int = Field(..., description="ID del documento asociado")
    id_area: int = Field(..., description="ID del área asignada (1=SuperAdmin, 2=Gerencia, 3=Juridica, 4=Coordinacion)")
    tipo_tarea: str = Field(..., description="REVISAR_JURIDICA, REVISAR_GERENCIA, FIRMAR, FINALIZAR")


class TareaPendienteUpdate(BaseModel):
    completada: Optional[bool] = None


class TareaPendienteOut(BaseModel):
    id: int
    id_documento: int
    id_area: int
    tipo_tarea: str
    fecha_asignacion: datetime
    completada: bool
