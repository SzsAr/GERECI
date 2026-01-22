"""
CRUD operations for observaciones
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.schemas.observaciones import ObservacionCreate, ObservacionUpdate

logger = logging.getLogger(__name__)


def create_observacion(db: Session, observacion: ObservacionCreate) -> Optional[int]:
    """
    Crear una nueva observación.
    Retorna el ID de la observación creada.
    """
    try:
        query = text("""
            INSERT INTO observaciones (
                id_documento, id_usuario, tipo, descripcion
            ) VALUES (
                :id_documento, :id_usuario, :tipo, :descripcion
            )
        """)
        
        params = {
            "id_documento": observacion.id_documento,
            "id_usuario": observacion.id_usuario,
            "tipo": observacion.tipo,
            "descripcion": observacion.descripcion
        }
        
        result = db.execute(query, params)
        db.commit()
        
        return result.lastrowid
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear observación: {e}")
        raise Exception("Error de base de datos al crear la observación")


def get_observacion_by_id(db: Session, observacion_id: int):
    """
    Obtener observación por ID.
    """
    try:
        query = text("""
            SELECT 
                id, id_documento, id_usuario, fecha, tipo, descripcion
            FROM observaciones 
            WHERE id = :observacion_id
        """)
        
        result = db.execute(query, {"observacion_id": observacion_id}).mappings().first()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener observación: {e}")
        raise Exception("Error de base de datos al obtener la observación")


def get_observaciones_by_documento(db: Session, documento_id: int, 
                                    tipo: Optional[str] = None) -> List:
    """
    Obtener todas las observaciones de un documento.
    Opcionalmente filtrar por tipo (JURIDICA o GERENCIA).
    """
    try:
        query = """
            SELECT 
                id, id_documento, id_usuario, fecha, tipo, descripcion
            FROM observaciones 
            WHERE id_documento = :documento_id
        """
        
        params = {"documento_id": documento_id}
        
        if tipo:
            query += " AND tipo = :tipo"
            params["tipo"] = tipo
        
        query += " ORDER BY fecha DESC"
        
        result = db.execute(text(query), params).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener observaciones del documento: {e}")
        raise Exception("Error de base de datos al obtener observaciones")


def get_observaciones_by_usuario(db: Session, usuario_id: int) -> List:
    """
    Obtener todas las observaciones realizadas por un usuario.
    """
    try:
        query = text("""
            SELECT 
                id, id_documento, id_usuario, fecha, tipo, descripcion
            FROM observaciones 
            WHERE id_usuario = :usuario_id
            ORDER BY fecha DESC
        """)
        
        result = db.execute(query, {"usuario_id": usuario_id}).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener observaciones del usuario: {e}")
        raise Exception("Error de base de datos al obtener observaciones")


def update_observacion(db: Session, observacion_id: int, 
                       observacion_update: ObservacionUpdate) -> bool:
    """
    Actualizar una observación (solo la descripción).
    """
    try:
        fields = observacion_update.model_dump(exclude_unset=True)
        if not fields:
            return False
        
        set_clause = ", ".join([f"{key} = :{key}" for key in fields])
        fields["observacion_id"] = observacion_id
        
        query = text(f"UPDATE observaciones SET {set_clause} WHERE id = :observacion_id")
        db.execute(query, fields)
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar observación: {e}")
        raise Exception("Error de base de datos al actualizar la observación")


def delete_observacion(db: Session, observacion_id: int) -> bool:
    """
    Eliminar una observación.
    """
    try:
        query = text("DELETE FROM observaciones WHERE id = :observacion_id")
        db.execute(query, {"observacion_id": observacion_id})
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar observación: {e}")
        raise Exception("Error de base de datos al eliminar la observación")
