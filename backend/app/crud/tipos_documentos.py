"""
CRUD operations for tipos_documentos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def create_tipo_documento(db: Session, nombre: str, codigo: str, requiere_juridica: bool) -> Optional[int]:
    """Crear un nuevo tipo de documento"""
    try:
        query = text("""
            INSERT INTO tipos_documentos (nombre, codigo, requiere_juridica)
            VALUES (:nombre, :codigo, :requiere_juridica)
        """)
        result = db.execute(query, {
            "nombre": nombre,
            "codigo": codigo,
            "requiere_juridica": requiere_juridica
        })
        db.commit()
        return result.lastrowid
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear tipo de documento: {e}")
        raise Exception("Error de base de datos al crear tipo de documento")


def get_tipo_documento_by_id(db: Session, id: int):
    """Obtener un tipo de documento por ID"""
    try:
        query = text("""
            SELECT id, nombre, codigo, requiere_juridica
            FROM tipos_documentos
            WHERE id = :id
        """)
        result = db.execute(query, {"id": id}).mappings().first()
        return result
    except Exception as e:
        logger.error(f"Error al obtener tipo de documento: {e}")
        raise Exception("Error de base de datos al obtener tipo de documento")


def get_all_tipos_documentos(db: Session) -> List:
    """Obtener todos los tipos de documentos"""
    try:
        query = text("""
            SELECT id, nombre, codigo, requiere_juridica
            FROM tipos_documentos
            ORDER BY nombre ASC
        """)
        result = db.execute(query).mappings().all()
        return result
    except Exception as e:
        logger.error(f"Error al obtener tipos de documentos: {e}")
        raise Exception("Error de base de datos al obtener tipos de documentos")


def update_tipo_documento(db: Session, id: int, nombre: str = None, codigo: str = None, requiere_juridica: bool = None) -> bool:
    """Actualizar un tipo de documento"""
    try:
        updates = {}
        if nombre is not None:
            updates["nombre"] = nombre
        if codigo is not None:
            updates["codigo"] = codigo
        if requiere_juridica is not None:
            updates["requiere_juridica"] = requiere_juridica
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
        updates["id"] = id
        
        query = text(f"UPDATE tipos_documentos SET {set_clause} WHERE id = :id")
        result = db.execute(query, updates)
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar tipo de documento: {e}")
        raise Exception("Error de base de datos al actualizar tipo de documento")


def delete_tipo_documento(db: Session, id: int) -> bool:
    """Eliminar un tipo de documento"""
    try:
        query = text("DELETE FROM tipos_documentos WHERE id = :id")
        result = db.execute(query, {"id": id})
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar tipo de documento: {e}")
        raise Exception("Error de base de datos al eliminar tipo de documento")
