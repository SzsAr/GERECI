"""
Pydantic schemas for control_consecutivos
"""
from pydantic import BaseModel


class ConsecutivoOut(BaseModel):
    id_tipo_documento: int
    ultimo_numero: int


class ConsecutivoCreate(BaseModel):
    id_tipo_documento: int
    numero_inicial: int = 0


class ConsecutivoReset(BaseModel):
    nuevo_numero: int
