"""
CRUD operations for documentos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.schemas.documentos import DocumentoCreate, DocumentoUpdate

logger = logging.getLogger(__name__)


def create_documento(db: Session, documento: DocumentoCreate, usuario_genera: int) -> Optional[int]:
    """
    Crear un nuevo documento en estado BORRADOR.
    Retorna el ID del documento creado.
    """
    try:
        query = text("""
            INSERT INTO documentos (
                id_tipo, id_plantilla, usuario_genera,
                Asunto, estado
            ) VALUES (
                :id_tipo, :id_plantilla, :usuario_genera,
                :asunto, 'BORRADOR'
            )
        """)
        
        params = {
            "id_tipo": documento.id_tipo,
            "id_plantilla": documento.id_plantilla,
            "usuario_genera": usuario_genera,
            "asunto": documento.asunto
        }
        
        result = db.execute(query, params)
        db.commit()
        
        # Retornar el ID del documento creado
        return result.lastrowid
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear documento: {e}")
        raise Exception("Error de base de datos al crear el documento")


def get_documento_by_id(db: Session, documento_id: int):
    """
    Obtener documento por ID.
    """
    try:
        query = text("""
            SELECT 
                id, id_tipo, id_plantilla, usuario_genera,
                Asunto AS asunto, consecutivo, fecha_creacion, fecha_emision,
                ruta_word_generado, ruta_pdf_final, estado
            FROM documentos 
            WHERE id = :documento_id
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().first()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener documento: {e}")
        raise Exception("Error de base de datos al obtener el documento")


def get_all_documentos(db: Session, filtro_estado: Optional[str] = None, 
                       filtro_usuario: Optional[int] = None) -> List:
    """
    Obtener todos los documentos, con filtros opcionales por estado o usuario.
    """
    try:
        query = """
            SELECT 
                id, id_tipo, id_plantilla, usuario_genera,
                Asunto AS asunto, consecutivo, fecha_creacion, fecha_emision,
                ruta_word_generado, ruta_pdf_final, estado
            FROM documentos 
            WHERE 1=1
        """
        
        params = {}
        
        if filtro_estado:
            query += " AND estado = :estado"
            params["estado"] = filtro_estado
        
        if filtro_usuario:
            query += " AND usuario_genera = :usuario"
            params["usuario"] = filtro_usuario
        
        query += " ORDER BY fecha_creacion DESC"
        
        result = db.execute(text(query), params).mappings().all()
        return result
    
    except Exception as e:
        logger.error(f"Error al obtener documentos: {e}")
        raise Exception("Error de base de datos al obtener documentos")


def update_documento(db: Session, documento_id: int, 
                     documento_update: DocumentoUpdate) -> bool:
    """
    Actualizar campos del documento (no el estado).
    """
    try:
        fields = documento_update.model_dump(exclude_unset=True)
        if not fields:
            return False
        
        set_clause = ", ".join([f"{key} = :{key}" for key in fields])
        fields["documento_id"] = documento_id
        
        query = text(f"UPDATE documentos SET {set_clause} WHERE id = :documento_id")
        db.execute(query, fields)
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar documento: {e}")
        raise Exception("Error de base de datos al actualizar el documento")


def cambiar_estado_documento(db: Session, documento_id: int, nuevo_estado: str) -> bool:
    """
    Cambiar el estado de un documento.
    Estados válidos: BORRADOR, EN_REVISION_JURIDICA, EN_REVISION_GERENCIAL, 
                     APROBADO_JURIDICA, FIRMADO, DEVUELTO_JURIDICA, 
                     DEVUELTO_GERENCIA, PENDIENTE_FINALIZACION, FINALIZADO
    """
    try:
        estados_validos = [
            'BORRADOR', 'EN_REVISION_JURIDICA', 'EN_REVISION_GERENCIAL',
            'APROBADO_JURIDICA', 'FIRMADO', 'DEVUELTO_JURIDICA',
            'DEVUELTO_GERENCIA', 'PENDIENTE_FINALIZACION', 'FINALIZADO'
        ]
        
        if nuevo_estado not in estados_validos:
            raise ValueError(f"Estado inválido: {nuevo_estado}")
        
        # Si es FINALIZADO, también actualizar fecha_emision
        if nuevo_estado == 'FINALIZADO':
            query = text("""
                UPDATE documentos 
                SET estado = :nuevo_estado, fecha_emision = NOW()
                WHERE id = :documento_id
            """)
        else:
            query = text("""
                UPDATE documentos 
                SET estado = :nuevo_estado 
                WHERE id = :documento_id
            """)
        
        db.execute(query, {
            "nuevo_estado": nuevo_estado,
            "documento_id": documento_id
        })
        db.commit()
        return True
    
    except ValueError as e:
        logger.error(f"Error: {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al cambiar estado del documento: {e}")
        raise Exception("Error de base de datos al cambiar estado")


def asignar_consecutivo(db: Session, documento_id: int, tipo_documento_id: int) -> str:
    """
    Asignar consecutivo automático al documento.
    Se llama cuando el documento es FINALIZADO.
    Retorna el consecutivo asignado.
    """
    try:
        # Obtener el siguiente número de control_consecutivos
        query_get = text("""
            SELECT ultimo_numero FROM control_consecutivos 
            WHERE id_tipo_documento = :tipo_id
        """)
        
        result = db.execute(query_get, {"tipo_id": tipo_documento_id}).fetchone()
        
        if result is None:
            # Si no existe registro, crear uno
            query_insert = text("""
                INSERT INTO control_consecutivos (id_tipo_documento, ultimo_numero)
                VALUES (:tipo_id, 1)
            """)
            db.execute(query_insert, {"tipo_id": tipo_documento_id})
            siguiente_numero = 1
        else:
            siguiente_numero = result.ultimo_numero + 1
        
        # Obtener código del tipo de documento
        query_tipo = text("""
            SELECT codigo FROM tipos_documentos WHERE id = :tipo_id
        """)
        
        tipo_result = db.execute(query_tipo, {"tipo_id": tipo_documento_id}).fetchone()
        codigo_tipo = tipo_result.codigo if tipo_result else "X"
        
        # Generar consecutivo: CODIGO-NUMERO (ej: R-001)
        consecutivo = f"{codigo_tipo}-{str(siguiente_numero).zfill(3)}"
        
        # Actualizar control_consecutivos
        query_update = text("""
            UPDATE control_consecutivos 
            SET ultimo_numero = :nuevo_numero 
            WHERE id_tipo_documento = :tipo_id
        """)
        
        db.execute(query_update, {
            "nuevo_numero": siguiente_numero,
            "tipo_id": tipo_documento_id
        })
        
        # Actualizar documento con el consecutivo
        query_doc = text("""
            UPDATE documentos 
            SET consecutivo = :consecutivo 
            WHERE id = :documento_id
        """)
        
        db.execute(query_doc, {
            "consecutivo": consecutivo,
            "documento_id": documento_id
        })
        
        db.commit()
        return consecutivo
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al asignar consecutivo: {e}")
        raise Exception("Error de base de datos al asignar consecutivo")


def necesita_revision_juridica(db: Session, tipo_documento_id: int) -> bool:
    """
    Verificar si un tipo de documento requiere revisión jurídica.
    """
    try:
        query = text("""
            SELECT requiere_juridica FROM tipos_documentos 
            WHERE id = :tipo_id
        """)
        
        result = db.execute(query, {"tipo_id": tipo_documento_id}).fetchone()
        
        if result is None:
            return False
        
        return result.requiere_juridica
    
    except Exception as e:
        logger.error(f"Error al verificar si necesita revisión jurídica: {e}")
        raise Exception("Error de base de datos")
