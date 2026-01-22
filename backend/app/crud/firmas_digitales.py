"""
CRUD operations for firmas_digitales
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.schemas.firmas_digitales import FirmaDigitalCreate

logger = logging.getLogger(__name__)


def create_firma_digital(db: Session, firma: FirmaDigitalCreate) -> Optional[int]:
    """
    Registrar una firma digital.
    Solo puede haber una firma por documento (constraint UNIQUE).
    Retorna el ID de la firma creada.
    """
    try:
        # Verificar que el documento no esté firmado
        query_check = text("""
            SELECT id FROM firmas_digitales 
            WHERE id_documento = :id_documento
        """)
        
        existing = db.execute(query_check, {"id_documento": firma.id_documento}).fetchone()
        
        if existing:
            raise Exception("Este documento ya tiene una firma digital registrada")
        
        # Insertar firma
        query = text("""
            INSERT INTO firmas_digitales (
                id_usuario, id_documento
            ) VALUES (
                :id_usuario, :id_documento
            )
        """)
        
        params = {
            "id_usuario": firma.id_usuario,
            "id_documento": firma.id_documento
        }
        
        result = db.execute(query, params)
        db.commit()
        
        return result.lastrowid
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear firma digital: {e}")
        raise Exception(str(e))


def get_firma_by_id(db: Session, firma_id: int):
    """
    Obtener firma digital por ID.
    """
    try:
        query = text("""
            SELECT 
                id, id_usuario, id_documento, fecha_firma
            FROM firmas_digitales 
            WHERE id = :firma_id
        """)
        
        result = db.execute(query, {"firma_id": firma_id}).mappings().first()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener firma digital: {e}")
        raise Exception("Error de base de datos al obtener la firma digital")


def get_firma_by_documento(db: Session, documento_id: int):
    """
    Obtener firma digital de un documento.
    Solo puede haber una firma por documento.
    """
    try:
        query = text("""
            SELECT 
                id, id_usuario, id_documento, fecha_firma
            FROM firmas_digitales 
            WHERE id_documento = :documento_id
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().first()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener firma del documento: {e}")
        raise Exception("Error de base de datos al obtener la firma")


def get_firmas_by_usuario(db: Session, usuario_id: int) -> List:
    """
    Obtener todas las firmas digitales realizadas por un usuario.
    """
    try:
        query = text("""
            SELECT 
                id, id_usuario, id_documento, fecha_firma
            FROM firmas_digitales 
            WHERE id_usuario = :usuario_id
            ORDER BY fecha_firma DESC
        """)
        
        result = db.execute(query, {"usuario_id": usuario_id}).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener firmas del usuario: {e}")
        raise Exception("Error de base de datos al obtener firmas del usuario")


def delete_firma_digital(db: Session, firma_id: int) -> bool:
    """
    Eliminar una firma digital.
    """
    try:
        query = text("DELETE FROM firmas_digitales WHERE id = :firma_id")
        db.execute(query, {"firma_id": firma_id})
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar firma digital: {e}")
        raise Exception("Error de base de datos al eliminar la firma digital")
