"""
CRUD operations for tareas_pendientes
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.schemas.tareas_pendientes import TareaPendienteCreate

logger = logging.getLogger(__name__)


def create_tarea(db: Session, tarea: TareaPendienteCreate) -> Optional[int]:
    """
    Crear una nueva tarea pendiente.
    Retorna el ID de la tarea creada.
    """
    try:
        query = text("""
            INSERT INTO tareas_pendientes (
                id_documento, id_area, tipo_tarea, completada
            ) VALUES (
                :id_documento, :id_area, :tipo_tarea, FALSE
            )
        """)
        
        params = {
            "id_documento": tarea.id_documento,
            "id_area": tarea.id_area,
            "tipo_tarea": tarea.tipo_tarea
        }
        
        result = db.execute(query, params)
        db.commit()
        
        return result.lastrowid
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear tarea pendiente: {e}")
        raise Exception("Error de base de datos al crear la tarea pendiente")


def get_tarea_by_id(db: Session, tarea_id: int):
    """
    Obtener tarea pendiente por ID.
    """
    try:
        query = text("""
            SELECT 
                id, id_documento, id_area, tipo_tarea,
                fecha_asignacion, completada
            FROM tareas_pendientes 
            WHERE id = :tarea_id
        """)
        
        result = db.execute(query, {"tarea_id": tarea_id}).mappings().first()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener tarea pendiente: {e}")
        raise Exception("Error de base de datos al obtener la tarea pendiente")


def get_tareas_by_area(db: Session, area_id: int, 
                        solo_pendientes: bool = False) -> List:
    """
    Obtener todas las tareas de un área.
    Si solo_pendientes=True, solo devuelve las no completadas.
    """
    try:
        query = """
            SELECT 
                id, id_documento, id_area, tipo_tarea,
                fecha_asignacion, completada
            FROM tareas_pendientes 
            WHERE id_area = :area_id
        """
        
        params = {"area_id": area_id}
        
        if solo_pendientes:
            query += " AND completada = FALSE"
        
        query += " ORDER BY fecha_asignacion DESC"
        
        result = db.execute(text(query), params).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener tareas de área: {e}")
        raise Exception("Error de base de datos al obtener tareas")


def get_tareas_by_documento(db: Session, documento_id: int) -> List:
    """
    Obtener todas las tareas asociadas a un documento.
    """
    try:
        query = text("""
            SELECT 
                id, id_documento, id_area, tipo_tarea,
                fecha_asignacion, completada
            FROM tareas_pendientes 
            WHERE id_documento = :documento_id
            ORDER BY fecha_asignacion ASC
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener tareas del documento: {e}")
        raise Exception("Error de base de datos al obtener tareas del documento")


def completar_tarea(db: Session, tarea_id: int) -> bool:
    """
    Marcar una tarea como completada.
    """
    try:
        query = text("""
            UPDATE tareas_pendientes 
            SET completada = TRUE 
            WHERE id = :tarea_id
        """)
        
        db.execute(query, {"tarea_id": tarea_id})
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al completar tarea: {e}")
        raise Exception("Error de base de datos al completar la tarea")


def delete_tarea(db: Session, tarea_id: int) -> bool:
    """
    Eliminar una tarea pendiente.
    """
    try:
        query = text("DELETE FROM tareas_pendientes WHERE id = :tarea_id")
        db.execute(query, {"tarea_id": tarea_id})
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar tarea: {e}")
        raise Exception("Error de base de datos al eliminar la tarea")
