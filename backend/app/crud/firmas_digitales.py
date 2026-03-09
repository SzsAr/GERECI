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
    Un documento puede tener múltiples firmas, pero un usuario no puede firmar dos veces.
    Retorna el ID de la firma creada.
    """
    try:
        # Verificar que el usuario no haya firmado ya este documento
        query_check = text("""
            SELECT id FROM firmas_digitales 
            WHERE id_documento = :id_documento AND id_usuario = :id_usuario
        """)
        
        existing = db.execute(query_check, {
            "id_documento": firma.id_documento,
            "id_usuario": firma.id_usuario
        }).fetchone()
        
        if existing:
            raise Exception("Este usuario ya ha firmado el documento")
        
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


def get_firmas_by_documento(db: Session, documento_id: int):
    """
    Obtener todas las firmas digitales de un documento con información completa.
    Incluye nombre del usuario, cargo, rol e imagen de firma.
    """
    try:
        query = text("""
            SELECT 
                f.id, f.id_usuario, f.id_documento, f.fecha_firma,
                u.nombre as nombre_usuario,
                u.id_rol as id_rol,
                COALESCE(c.nombre, 'Sin cargo asignado') as cargo,
                u.firma as firma_imagen
            FROM firmas_digitales f
            INNER JOIN usuarios u ON f.id_usuario = u.id
            LEFT JOIN cargos c ON u.id_cargo = c.id
            WHERE f.id_documento = :documento_id
            ORDER BY f.fecha_firma ASC
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().all()
        return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Error al obtener firmas del documento: {e}")
        raise Exception("Error de base de datos al obtener firmas")


def registrar_firma_aprobacion(db: Session, documento_id: int, usuario_id: int) -> Optional[int]:
    """
    Registrar firma automática cuando un usuario aprueba un documento.
    No lanza excepción si el usuario ya firmó (para permitir múltiples cambios de estado).
    
    Returns:
        ID de la firma creada, o None si ya existía
    """
    try:
        # Verificar si el usuario ya firmó
        query_check = text("""
            SELECT id FROM firmas_digitales 
            WHERE id_documento = :id_documento AND id_usuario = :id_usuario
        """)
        
        existing = db.execute(query_check, {
            "id_documento": documento_id,
            "id_usuario": usuario_id
        }).fetchone()
        
        if existing:
            logger.info(f"Usuario {usuario_id} ya había firmado documento {documento_id}")
            return None
        
        # Insertar firma
        query = text("""
            INSERT INTO firmas_digitales (
                id_usuario, id_documento
            ) VALUES (
                :id_usuario, :id_documento
            )
        """)
        
        result = db.execute(query, {
            "id_usuario": usuario_id,
            "id_documento": documento_id
        })
        db.commit()
        
        logger.info(f"Firma registrada: usuario {usuario_id} en documento {documento_id}")
        return result.lastrowid
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al registrar firma de aprobación: {e}")
        # No lanzar excepción, solo loggear el error
        return None
    
    except Exception as e:
        logger.error(f"Error al obtener firmas del documento: {e}")
        raise Exception("Error de base de datos al obtener las firmas")


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


def verificar_firmas_requeridas(db: Session, documento_id: int):
    """
    Verificar qué firmas hacen falta según el tipo de documento.
    
    Reglas:
    - Normativas (requiere_juridica=0): Necesita firma de la unidad creadora y del gerente
    - Resoluciones (requiere_juridica=1): Necesita firma de la unidad, jurídica y gerente
    
    Retorna información de qué firmas faltan y si el documento está listo para finalizarse.
    """
    try:
        # Obtener información del documento y sus firmas actuales
        query = text("""
            SELECT 
                d.id,
                d.usuario_genera,
                td.requiere_juridica,
                (SELECT COUNT(*) FROM firmas_digitales WHERE id_documento = d.id) as total_firmas,
                (SELECT COUNT(*) FROM firmas_digitales f 
                 INNER JOIN usuarios u ON f.id_usuario = u.id 
                 WHERE f.id_documento = d.id AND u.id_rol = 2) as firmas_gerencia,
                (SELECT COUNT(*) FROM firmas_digitales f 
                 INNER JOIN usuarios u ON f.id_usuario = u.id 
                 WHERE f.id_documento = d.id AND u.id_rol = 3) as firmas_juridica,
                (SELECT COUNT(*) FROM firmas_digitales f 
                 WHERE f.id_documento = d.id AND f.id_usuario = d.usuario_genera) as firmas_creador
            FROM documentos d
            INNER JOIN tipos_documentos td ON d.id_tipo_documento = td.id
            WHERE d.id = :documento_id
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().first()
        
        if not result:
            raise Exception("Documento no encontrado")
        
        requiere_juridica = bool(result['requiere_juridica'])
        firmas_gerencia = result['firmas_gerencia']
        firmas_juridica = result['firmas_juridica']
        firmas_creador = result['firmas_creador']
        
        firmas_faltantes = []
        
        # Verificar firma del creador
        if firmas_creador == 0:
            firmas_faltantes.append("Falta firma de la unidad creadora del documento")
        
        # Verificar firma de gerencia
        if firmas_gerencia == 0:
            firmas_faltantes.append("Falta firma de Gerencia")
        
        # Verificar firma de jurídica solo si el documento lo requiere
        if requiere_juridica and firmas_juridica == 0:
            firmas_faltantes.append("Falta firma de Jurídica")
        
        # Determinar si está listo
        if requiere_juridica:
            # Resolución: necesita las 3 firmas
            listo = firmas_creador > 0 and firmas_gerencia > 0 and firmas_juridica > 0
        else:
            # Normativa: necesita 2 firmas (creador + gerencia)
            listo = firmas_creador > 0 and firmas_gerencia > 0
        
        return {
            "documento_id": documento_id,
            "requiere_juridica": requiere_juridica,
            "firmas_actuales": result['total_firmas'],
            "firmas_requeridas": 3 if requiere_juridica else 2,
            "tiene_firma_creador": firmas_creador > 0,
            "tiene_firma_gerencia": firmas_gerencia > 0,
            "tiene_firma_juridica": firmas_juridica > 0,
            "firmas_faltantes": firmas_faltantes,
            "listo_para_finalizar": listo
        }
    
    except Exception as e:
        logger.error(f"Error al verificar firmas requeridas: {e}")
        raise Exception(str(e))
