"""
CRUD operations for plantillas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging
import json

logger = logging.getLogger(__name__)


def create_plantilla(db: Session, id_tipo: int, nombre: str, nombre_archivo: str, ruta_almacenamiento: Optional[str], campos_json: Optional[dict]) -> Optional[int]:
    """Crear una plantilla"""
    try:
        campos_serializados = json.dumps(campos_json) if isinstance(campos_json, dict) else campos_json
        query = text(
            """
            INSERT INTO plantillas (id_tipo, nombre, nombre_archivo, ruta_almacenamiento, campos_json)
            VALUES (:id_tipo, :nombre, :nombre_archivo, :ruta_almacenamiento, :campos_json)
            """
        )
        result = db.execute(query, {
            "id_tipo": id_tipo,
            "nombre": nombre,
            "nombre_archivo": nombre_archivo,
            "ruta_almacenamiento": ruta_almacenamiento,
            "campos_json": campos_serializados
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
            SELECT p.id, p.id_tipo, p.nombre, p.nombre_archivo, 
                   p.ruta_almacenamiento, p.campos_json,
                   t.nombre AS tipo_nombre
            FROM plantillas p
            LEFT JOIN tipos_documentos t ON p.id_tipo = t.id
            WHERE p.id = :id
            """
        )
        result = db.execute(query, {"id": plantilla_id}).mappings().first()
        if result and result.get("campos_json") and isinstance(result["campos_json"], str):
            try:
                result = dict(result)
                result["campos_json"] = json.loads(result["campos_json"])
            except json.JSONDecodeError:
                pass
        return result
    except Exception as e:
        logger.error(f"Error al obtener plantilla: {e}")
        raise Exception("Error de base de datos al obtener plantilla")


def get_all_plantillas(db: Session) -> List:
    """Obtener todas las plantillas"""
    try:
        query = text(
            """
            SELECT p.id, p.id_tipo, p.nombre, p.nombre_archivo, 
                   p.ruta_almacenamiento, p.campos_json,
                   t.nombre AS tipo_nombre
            FROM plantillas p
            LEFT JOIN tipos_documentos t ON p.id_tipo = t.id
            ORDER BY p.id ASC
            """
        )
        result = db.execute(query).mappings().all()
        # Deserializar campos_json si viene como string
        parsed = []
        for row in result:
            row_dict = dict(row)
            if row_dict.get("campos_json") and isinstance(row_dict["campos_json"], str):
                try:
                    row_dict["campos_json"] = json.loads(row_dict["campos_json"])
                except json.JSONDecodeError:
                    pass
            parsed.append(row_dict)
        return parsed
    except Exception as e:
        logger.error(f"Error al obtener plantillas: {e}")
        raise Exception("Error de base de datos al obtener plantillas")


def update_plantilla(db: Session, plantilla_id: int, id_tipo: Optional[int] = None, nombre: Optional[str] = None, nombre_archivo: Optional[str] = None, ruta_almacenamiento: Optional[str] = None, campos_json: Optional[dict] = None) -> bool:
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
        if campos_json is not None:
            updates["campos_json"] = json.dumps(campos_json) if isinstance(campos_json, dict) else campos_json

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
