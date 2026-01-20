"""
CRUD operations for plantillas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def create_plantilla(db: Session, id_tipo: int, nombre: str, nombre_archivo: str, ruta_almacenamiento: Optional[str]) -> Optional[int]:
    """Crear una plantilla"""
    try:
        query = text(
            """
            INSERT INTO plantillas (id_tipo, nombre, nombre_archivo, ruta_almacenamiento)
            VALUES (:id_tipo, :nombre, :nombre_archivo, :ruta_almacenamiento)
            """
        )
        result = db.execute(query, {
            "id_tipo": id_tipo,
            "nombre": nombre,
            "nombre_archivo": nombre_archivo,
            "ruta_almacenamiento": ruta_almacenamiento
        })
        db.commit()
        return result.lastrowid
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear plantilla: {e}")
        raise Exception("Error de base de datos al crear plantilla")


def get_plantilla_by_id(db: Session, plantilla_id: int):
    """Obtener una plantilla por ID"""
    try:
        query = text(
            """
            SELECT id, id_tipo, nombre, nombre_archivo, ruta_almacenamiento
            FROM plantillas
            WHERE id = :id
            """
        )
        result = db.execute(query, {"id": plantilla_id}).mappings().first()
        return result
    except Exception as e:
        logger.error(f"Error al obtener plantilla: {e}")
        raise Exception("Error de base de datos al obtener plantilla")


def get_all_plantillas(db: Session) -> List:
    """Obtener todas las plantillas"""
    try:
        query = text(
            """
            SELECT id, id_tipo, nombre, nombre_archivo, ruta_almacenamiento
            FROM plantillas
            ORDER BY nombre ASC
            """
        )
        result = db.execute(query).mappings().all()
        return result
    except Exception as e:
        logger.error(f"Error al obtener plantillas: {e}")
        raise Exception("Error de base de datos al obtener plantillas")


def update_plantilla(db: Session, plantilla_id: int, id_tipo: Optional[int] = None, nombre: Optional[str] = None, nombre_archivo: Optional[str] = None, ruta_almacenamiento: Optional[str] = None) -> bool:
    """Actualizar una plantilla"""
    try:
        updates = {}
        if id_tipo is not None:
            updates["id_tipo"] = id_tipo
        if nombre is not None:
            updates["nombre"] = nombre
        if nombre_archivo is not None:
            updates["nombre_archivo"] = nombre_archivo
        if ruta_almacenamiento is not None:
            updates["ruta_almacenamiento"] = ruta_almacenamiento

        if not updates:
            return False

        set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
        updates["id"] = plantilla_id

        query = text(f"UPDATE plantillas SET {set_clause} WHERE id = :id")
        result = db.execute(query, updates)
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar plantilla: {e}")
        raise Exception("Error de base de datos al actualizar plantilla")


def delete_plantilla(db: Session, plantilla_id: int) -> bool:
    """Eliminar una plantilla"""
    try:
        query = text("DELETE FROM plantillas WHERE id = :id")
        result = db.execute(query, {"id": plantilla_id})
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar plantilla: {e}")
        raise Exception("Error de base de datos al eliminar plantilla")
