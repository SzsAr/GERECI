"""
CRUD operations for control_consecutivos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def create_consecutivo(db: Session, id_tipo_documento: int, numero_inicial: int = 0) -> bool:
    """Crear control de consecutivo para un tipo de documento"""
    try:
        # Evitar violar PK compuesta (id_tipo_documento único)
        exists_query = text("""
            SELECT 1 FROM control_consecutivos WHERE id_tipo_documento = :id_tipo_documento
        """)
        if db.execute(exists_query, {"id_tipo_documento": id_tipo_documento}).scalar():
            return False

        query = text("""
            INSERT INTO control_consecutivos (id_tipo_documento, ultimo_numero)
            VALUES (:id_tipo_documento, :numero_inicial)
        """)
        db.execute(query, {
            "id_tipo_documento": id_tipo_documento,
            "numero_inicial": numero_inicial
        })
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Consecutivo duplicado: {e}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear control de consecutivo: {e}")
        raise Exception("Error de base de datos al crear control de consecutivo")


def get_consecutivo_by_id_tipo(db: Session, id_tipo_documento: int):
    """Obtener consecutivo por tipo de documento"""
    try:
        query = text("""
            SELECT id_tipo_documento, ultimo_numero
            FROM control_consecutivos
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        result = db.execute(query, {"id_tipo_documento": id_tipo_documento}).mappings().first()
        return result
    except Exception as e:
        logger.error(f"Error al obtener consecutivo: {e}")
        raise Exception("Error de base de datos al obtener consecutivo")


def get_all_consecutivos(db: Session) -> List:
    """Obtener todos los consecutivos"""
    try:
        query = text("""
            SELECT id_tipo_documento, ultimo_numero
            FROM control_consecutivos
            ORDER BY id_tipo_documento ASC
        """)
        result = db.execute(query).mappings().all()
        return result
    except Exception as e:
        logger.error(f"Error al obtener consecutivos: {e}")
        raise Exception("Error de base de datos al obtener consecutivos")


def get_siguiente_numero(db: Session, id_tipo_documento: int) -> int:
    """Obtener el siguiente número consecutivo sin incrementar"""
    try:
        query = text("""
            SELECT ultimo_numero
            FROM control_consecutivos
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        result = db.execute(query, {"id_tipo_documento": id_tipo_documento}).scalar()
        
        if result is None:
            return 0
        
        return result + 1
    except Exception as e:
        logger.error(f"Error al obtener siguiente número: {e}")
        raise Exception("Error de base de datos al obtener siguiente número")


def incrementar_consecutivo(db: Session, id_tipo_documento: int) -> int:
    """Incrementar el consecutivo y retornar el nuevo número"""
    try:
        # Actualizar incrementando en 1
        query_update = text("""
            UPDATE control_consecutivos
            SET ultimo_numero = ultimo_numero + 1
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        result = db.execute(query_update, {"id_tipo_documento": id_tipo_documento})
        
        if result.rowcount == 0:
            # Si no existe, crearlo con 1
            create_consecutivo(db, id_tipo_documento, 1)
            return 1
        
        # Obtener el nuevo número
        query_select = text("""
            SELECT ultimo_numero
            FROM control_consecutivos
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        nuevo_numero = db.execute(query_select, {"id_tipo_documento": id_tipo_documento}).scalar()
        
        db.commit()
        return nuevo_numero
    except Exception as e:
        db.rollback()
        logger.error(f"Error al incrementar consecutivo: {e}")
        raise Exception("Error de base de datos al incrementar consecutivo")


def reset_consecutivo(db: Session, id_tipo_documento: int, nuevo_numero: int) -> bool:
    """Reiniciar/cambiar manualmente el consecutivo a un número específico"""
    try:
        query = text("""
            UPDATE control_consecutivos
            SET ultimo_numero = :nuevo_numero
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        result = db.execute(query, {
            "nuevo_numero": nuevo_numero,
            "id_tipo_documento": id_tipo_documento
        })
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al resetear consecutivo: {e}")
        raise Exception("Error de base de datos al resetear consecutivo")


def delete_consecutivo(db: Session, id_tipo_documento: int) -> bool:
    """Eliminar control de consecutivo"""
    try:
        query = text("""
            DELETE FROM control_consecutivos
            WHERE id_tipo_documento = :id_tipo_documento
        """)
        result = db.execute(query, {"id_tipo_documento": id_tipo_documento})
        db.commit()
        return result.rowcount > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar consecutivo: {e}")
        raise Exception("Error de base de datos al eliminar consecutivo")
