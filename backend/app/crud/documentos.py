"""
CRUD operations for documentos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging
import json

from app.schemas.documentos import DocumentoCreate, DocumentoUpdate

logger = logging.getLogger(__name__)


def create_documento(db: Session, documento: DocumentoCreate, usuario_genera: int) -> Optional[int]:
    """
    Crear un nuevo documento en estado BORRADOR.
    Retorna el ID del documento creado.
    """
    try:
        # Serializar valores_campos si vienen como dict
        valores_campos_json = None
        if documento.valores_campos:
            valores_campos_json = json.dumps(documento.valores_campos)
        
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
    Obtener documento por ID con información de tipo, plantilla y usuario.
    """
    try:
        query = text("""
            SELECT 
                d.id, d.id_tipo, d.id_plantilla, d.usuario_genera,
                d.Asunto AS asunto, d.consecutivo, d.fecha_creacion, d.fecha_emision,
                d.ruta_word_generado, d.ruta_pdf_final, d.estado,
                t.nombre AS tipo_nombre,
                p.nombre AS plantilla_nombre,
                u.nombre AS usuario_nombre
            FROM documentos d
            LEFT JOIN tipos_documentos t ON d.id_tipo = t.id
            LEFT JOIN plantillas p ON d.id_plantilla = p.id
            LEFT JOIN usuarios u ON d.usuario_genera = u.id_usuario
            WHERE d.id = :documento_id
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
    Incluye información de tipo, plantilla y usuario.
    """
    try:
        query = """
            SELECT 
                d.id, d.id_tipo, d.id_plantilla, d.usuario_genera,
                d.Asunto AS asunto, d.consecutivo, d.fecha_creacion, 
                CAST(d.fecha_emision AS DATETIME) AS fecha_emision,
                d.ruta_word_generado, d.ruta_pdf_final, d.estado,
                t.nombre AS tipo_nombre,
                p.nombre AS plantilla_nombre,
                u.nombre AS usuario_nombre
            FROM documentos d
            LEFT JOIN tipos_documentos t ON d.id_tipo = t.id
            LEFT JOIN plantillas p ON d.id_plantilla = p.id
            LEFT JOIN usuarios u ON d.usuario_genera = u.id_usuario
            WHERE 1=1
        """
        
        params = {}
        
        if filtro_estado:
            query += " AND d.estado = :estado"
            params["estado"] = filtro_estado
        
        if filtro_usuario:
            query += " AND d.usuario_genera = :usuario"
            params["usuario"] = filtro_usuario
        
        query += " ORDER BY d.fecha_creacion DESC"
        
        result = db.execute(text(query), params).mappings().all()
        return [dict(row) for row in result]
    
    except Exception as e:
        logger.error(f"Error al obtener documentos: {e}")
        # Retornar lista vacía en lugar de lanzar excepción
        return []


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


def obtener_transiciones_validas(db: Session, documento_id: int, estado_actual: str) -> List[str]:
    """
    Obtener los estados válidos a los que puede transitar el documento.
    Valida según si el tipo requiere revisión jurídica.
    
    Returns:
        Lista de estados permitidos desde el estado actual
    """
    try:
        # Obtener documento y verificar si requiere revisión jurídica
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        requiere_juridica = necesita_revision_juridica(db, doc.id_tipo)
        
        # Mapear transiciones válidas según estado actual
        transiciones = {
            'BORRADOR': [
                'EN_REVISION_JURIDICA' if requiere_juridica else 'EN_REVISION_GERENCIAL'
            ],
            'EN_REVISION_JURIDICA': ['APROBADO_JURIDICA', 'DEVUELTO_JURIDICA'],
            'APROBADO_JURIDICA': ['EN_REVISION_GERENCIAL'],
            'DEVUELTO_JURIDICA': ['BORRADOR'],
            'EN_REVISION_GERENCIAL': ['APROBADO_GERENCIA', 'DEVUELTO_GERENCIA'],
            'APROBADO_GERENCIA': ['FIRMADO'],
            'DEVUELTO_GERENCIA': ['BORRADOR'],
            'FIRMADO': ['PENDIENTE_FINALIZACION'],
            'PENDIENTE_FINALIZACION': ['FINALIZADO'],
            'FINALIZADO': []
        }
        
        return transiciones.get(estado_actual, [])
    
    except Exception as e:
        logger.error(f"Error al obtener transiciones válidas: {e}")
        return []


def cambiar_estado_documento(db: Session, documento_id: int, nuevo_estado: str) -> bool:
    """
    Cambiar el estado de un documento validando transiciones.
    """
    try:
        # Obtener estado actual
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        estado_actual = doc.estado
        
        # Validar que sea una transición permitida
        transiciones_validas = obtener_transiciones_validas(db, documento_id, estado_actual)
        if nuevo_estado not in transiciones_validas:
            raise ValueError(
                f"Transición no permitida de {estado_actual} a {nuevo_estado}. "
                f"Estados válidos: {transiciones_validas}"
            )
        
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
        logger.error(f"Error de validación: {e}")
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
        
        return bool(result.requiere_juridica)
    
    except Exception as e:
        logger.error(f"Error al verificar si necesita revisión jurídica: {e}")
        raise Exception("Error de base de datos")
