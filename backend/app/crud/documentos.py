"""
CRUD operations for documentos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import logging
import json

from app.schemas.documentos import DocumentoCreate, DocumentoUpdate
from app.utils.dynamic_data import insertar_datos_documento_en_plantilla, obtener_datos_documento_de_plantilla
from app.crud.plantillas import get_plantilla_by_id

logger = logging.getLogger(__name__)


# Campos reservados/autogenerados que no deben venir desde el usuario
AUTO_SYSTEM_FIELDS = {
    "consecutivo",
    "fecha",
    "fecha_emision",
    "fecha_creacion",
    "gerente_firma",
    "gerente_nombre",
    "gerente_cargo",
    "unidad_firma",
    "unidad_nombre",
    "unidad_cargo",
    "juridica_firma",
    "juridica_nombre",
    "juridica_cargo",
}


def filtrar_campos_usuario(valores_campos: Optional[dict]) -> dict:
    """
    Remover del payload de usuario los campos automáticos/sistema.
    """
    if not isinstance(valores_campos, dict):
        return {}

    campos_limpios = {}
    for key, value in valores_campos.items():
        key_normalizada = str(key).strip().lower()
        if key_normalizada in AUTO_SYSTEM_FIELDS:
            continue
        campos_limpios[key] = value

    return campos_limpios


def create_documento(db: Session, documento: DocumentoCreate, usuario_genera: int) -> Optional[int]:
    """
    Crear un nuevo documento en estado BORRADOR.
    Inserta los datos en la tabla dinámica de la plantilla.
    Retorna el ID del documento creado.
    """
    try:
        # Ignorar campos automáticos enviados por el cliente
        valores_campos_limpios = filtrar_campos_usuario(documento.valores_campos)

        # Serializar valores_campos si vienen como dict
        valores_campos_json = None
        if valores_campos_limpios:
            valores_campos_json = json.dumps(valores_campos_limpios)
        
        query = text("""
            INSERT INTO documentos (
                id_tipo, id_plantilla, usuario_genera,
                Asunto, estado, valores_campos
            ) VALUES (
                :id_tipo, :id_plantilla, :usuario_genera,
                :asunto, 'BORRADOR', :valores_campos
            )
        """)
        
        params = {
            "id_tipo": documento.id_tipo,
            "id_plantilla": documento.id_plantilla,
            "usuario_genera": usuario_genera,
            "asunto": documento.asunto,
            "valores_campos": valores_campos_json
        }
        
        result = db.execute(query, params)
        db.commit()
        
        documento_id = result.lastrowid
        
        # Insertar datos en la tabla dinámica de la plantilla
        plantilla = get_plantilla_by_id(db, documento.id_plantilla)
        if plantilla and plantilla.get('nombre_tabla'):
            insertar_datos_documento_en_plantilla(
                db,
                documento.id_plantilla,
                documento_id,
                valores_campos_limpios,
                plantilla['nombre_tabla']
            )
        
        # Retornar el ID del documento creado
        return documento_id
    
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
                d.Asunto AS asunto, d.consecutivo, d.fecha_creacion, 
                CAST(d.fecha_emision AS DATETIME) AS fecha_emision,
                d.ruta_word_generado, d.ruta_pdf_final, d.estado,
                d.valores_campos,
                t.nombre AS tipo_nombre,
                p.nombre AS plantilla_nombre,
                u.nombre AS usuario_nombre,
                u.documento AS documento,
                c.nombre AS cargo
            FROM documentos d
            LEFT JOIN tipos_documentos t ON d.id_tipo = t.id
            LEFT JOIN plantillas p ON d.id_plantilla = p.id
            LEFT JOIN usuarios u ON d.usuario_genera = u.id
            LEFT JOIN cargos c ON u.id_cargo = c.id
            WHERE d.id = :documento_id
        """)
        
        result = db.execute(query, {"documento_id": documento_id}).mappings().first()
        if result:
            doc_dict = dict(result)
            # Convertir valores_campos JSON string a dict si existe
            if doc_dict.get('valores_campos') and isinstance(doc_dict['valores_campos'], str):
                doc_dict['valores_campos'] = json.loads(doc_dict['valores_campos'])
            return doc_dict
        return None
    
    except Exception as e:
        logger.error(f"Error al obtener documento: {e}")
        raise Exception(f"Error de base de datos al obtener el documento: {str(e)}")


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
                d.valores_campos,
                t.nombre AS tipo_nombre,
                p.nombre AS plantilla_nombre,
                u.nombre AS usuario_nombre
            FROM documentos d
            LEFT JOIN tipos_documentos t ON d.id_tipo = t.id
            LEFT JOIN plantillas p ON d.id_plantilla = p.id
            LEFT JOIN usuarios u ON d.usuario_genera = u.id
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
        docs = []
        for row in result:
            doc_dict = dict(row)
            # Convertir valores_campos JSON string a dict si existe
            if doc_dict.get('valores_campos') and isinstance(doc_dict['valores_campos'], str):
                doc_dict['valores_campos'] = json.loads(doc_dict['valores_campos'])
            docs.append(doc_dict)
        return docs
    
    except Exception as e:
        logger.error(f"Error al obtener documentos: {e}")
        # Retornar lista vacía en lugar de lanzar excepción
        return []


def update_documento(db: Session, documento_id: int, 
                     documento_update: DocumentoUpdate) -> bool:
    """
    Actualizar campos del documento (no el estado).
    Serializa valores_campos a JSON si es necesario.
    """
    try:
        fields = documento_update.model_dump(exclude_unset=True)
        if not fields:
            return False
        
        # Serializar valores_campos si existe
        if 'valores_campos' in fields and fields['valores_campos'] is not None:
            fields['valores_campos'] = json.dumps(
                filtrar_campos_usuario(fields['valores_campos'])
            )
        
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
    
    Estados disponibles en BD:
    - BORRADOR
    - EN_REVISION_JURIDICA
    - EN_REVISION_GERENCIAL
    - APROBADO_JURIDICA
    - DEVUELTO_JURIDICA
    - DEVUELTO_GERENCIA
    - FIRMADO
    - PENDIENTE_FINALIZACION
    - FINALIZADO
    
    Returns:
        Lista de estados permitidos desde el estado actual
    """
    try:
        # Obtener documento y verificar si requiere revisión jurídica
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        # Verificar tipo de documento y si requiere jurídica
        id_tipo = doc.get('id_tipo') if isinstance(doc, dict) else doc.id_tipo
        requiere_juridica = necesita_revision_juridica(db, id_tipo)
        
        # Mapear transiciones válidas según flujo:
        # CON JURÍDICA: BORRADOR → EN_REVISION_JURIDICA → (DEVUELTO_JURIDICA o APROBADO_JURIDICA) 
        #               → EN_REVISION_GERENCIAL → (APROBADO_GERENCIA o DEVUELTO_GERENCIA) → FIRMADO → FINALIZADO
        # SIN JURÍDICA: BORRADOR → EN_REVISION_GERENCIAL → (APROBADO_GERENCIA o DEVUELTO_GERENCIA) → FIRMADO → FINALIZADO
        
        transiciones = {
            'BORRADOR': ['EN_REVISION_JURIDICA' if requiere_juridica else 'EN_REVISION_GERENCIAL'],
            'EN_REVISION_JURIDICA': ['APROBADO_JURIDICA', 'DEVUELTO_JURIDICA'],
            'DEVUELTO_JURIDICA': ['EN_REVISION_JURIDICA'],
            'APROBADO_JURIDICA': ['EN_REVISION_GERENCIAL'],
            'EN_REVISION_GERENCIAL': ['APROBADO_GERENCIA', 'DEVUELTO_GERENCIA'],
            'APROBADO_GERENCIA': ['FIRMADO'],
            'DEVUELTO_GERENCIA': ['EN_REVISION_JURIDICA' if requiere_juridica else 'EN_REVISION_GERENCIAL'],
            'FIRMADO': ['FINALIZADO'],
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
    Las aprobaciones en etapas de revisión avanzan automáticamente:
    - APROBADO_JURIDICA → EN_REVISION_GERENCIAL (automático)
    - APROBADO_GERENCIA → FIRMADO (automático)
    Cuando se marca como FINALIZADO, regenera el documento con el consecutivo asignado.
    """
    try:
        # Obtener estado actual
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        estado_actual = doc['estado']
        
        # Validar que sea una transición permitida
        transiciones_validas = obtener_transiciones_validas(db, documento_id, estado_actual)
        if nuevo_estado not in transiciones_validas:
            raise ValueError(
                f"Transición no permitida de {estado_actual} a {nuevo_estado}. "
                f"Estados válidos: {transiciones_validas}"
            )
        
        # Determinar el estado final (puede haber pasos automáticos)
        estado_final = nuevo_estado
        
        # Transiciones automáticas después de aprobaciones
        if nuevo_estado == 'APROBADO_JURIDICA':
            # Después de aprobar en Jurídica, pasar automáticamente a EN_REVISION_GERENCIAL
            estado_final = 'EN_REVISION_GERENCIAL'
        elif nuevo_estado == 'APROBADO_GERENCIA':
            # Después de aprobar en Gerencia, pasar automáticamente a FIRMADO
            estado_final = 'FIRMADO'
        
        # Si es FINALIZADO, también actualizar fecha_emision
        if estado_final == 'FINALIZADO':
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
            "nuevo_estado": estado_final,
            "documento_id": documento_id
        })
        db.commit()
        
        # Si es FINALIZADO, regenerar el documento con el consecutivo asignado
        if estado_final == 'FINALIZADO':
            try:
                from app.utils.document_generator import generar_word_desde_plantilla
                from app.crud.plantillas import get_plantilla_by_id
                from pathlib import Path
                
                # Obtener documento actualizado (con consecutivo já asignado por el trigger)
                doc_actualizado = get_documento_by_id(db, documento_id)
                if not doc_actualizado:
                    logger.warning(f"Documento {documento_id} no encontrado para regeneracion")
                else:
                    # Obtener plantilla
                    plantilla = get_plantilla_by_id(db, doc_actualizado.get('id_plantilla'))
                    if plantilla and plantilla.get('ruta_almacenamiento'):
                        # Generar contexto completo con el consecutivo ya asignado
                        context = generar_context_con_firmas(db, documento_id)
                        
                        # Regenerar documento Word final
                        plantilla_path = plantilla.get('ruta_almacenamiento')
                        if Path(plantilla_path).exists():
                            generar_word_desde_plantilla(
                                plantilla_path,
                                documento_id,
                                context
                            )
                            logger.info(f"Documento {documento_id} regenerado con consecutivo {context.get('consecutivo')}")
                        else:
                            logger.warning(f"Plantilla no encontrada en {plantilla_path}")
                    else:
                        logger.warning(f"Plantilla no encontrada para documento {documento_id}")
            except Exception as e:
                logger.error(f"Error al regenerar documento {documento_id}: {e}")
                # No fallar el cambio de estado si hay error en regeneración
        
        # Log de transición automática si aplica
        if estado_final != nuevo_estado:
            logger.info(f"Transición automática: {nuevo_estado} → {estado_final}")
        
        return True
    
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        raise
    except IntegrityError as e:
        db.rollback()
        detalle = str(e).lower()
        logger.error(f"Error de integridad al cambiar estado del documento: {e}")

        if "consecutivo" in detalle or "duplicate entry" in detalle:
            raise Exception(
                "Conflicto de consecutivo al finalizar. "
                "Verifique trigger e indice de consecutivos por tipo de documento."
            )

        raise Exception("Error de integridad al cambiar estado")
    except Exception as e:
        db.rollback()
        logger.error(f"Error al cambiar estado del documento: {e}")
        raise Exception("Error de base de datos al cambiar estado")


def obtener_consecutivo_asignado(db: Session, documento_id: int) -> Optional[str]:
    """
    Obtener el consecutivo asignado por el trigger de la BD.
    El trigger asigna automáticamente al pasar a FINALIZADO.
    
    Returns:
        Consecutivo asignado o None si aún no tiene
    """
    try:
        query = text("""
            SELECT consecutivo FROM documentos WHERE id = :documento_id
        """)
        result = db.execute(query, {"documento_id": documento_id}).fetchone()
        return result.consecutivo if result else None
    except Exception as e:
        logger.error(f"Error al obtener consecutivo: {e}")
        return None


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


def obtener_datos_usuario(db: Session, usuario_id: int) -> dict:
    """
    Obtener nombre, cargo e imagen de firma de un usuario.
    """
    try:
        query = text("""
            SELECT 
                u.nombre,
                u.documento,
                u.firma,
                c.nombre AS cargo
            FROM usuarios u
            LEFT JOIN cargos c ON u.id_cargo = c.id
            WHERE u.id = :usuario_id
        """)
        
        result = db.execute(query, {"usuario_id": usuario_id}).mappings().first()
        
        if result:
            return dict(result)
        return {
            "nombre": "",
            "documento": "",
            "firma": None,
            "cargo": ""
        }
    
    except Exception as e:
        logger.error(f"Error al obtener datos del usuario: {e}")
        return {
            "nombre": "",
            "documento": "",
            "firma": None,
            "cargo": ""
        }


def generar_context_para_plantilla(db: Session, documento_id: int, usuario_id: Optional[int] = None) -> dict:
    """
    Generar el context completo para renderizar la plantilla con docxtpl.
    Incluye valores_campos + metadatos del documento + datos del usuario actual.
    
    Args:
        db: Sesión de BD
        documento_id: ID del documento
        usuario_id: ID del usuario actual (opcional, para incluir nombre, cargo, firma)
    
    Returns:
        Dict con todos los valores para la plantilla
    """
    try:
        # Obtener documento completo
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        # Extraer valores base
        context = {}
        
        # Si hay valores_campos, agregarlos al context
        if doc.get('valores_campos'):
            if isinstance(doc['valores_campos'], dict):
                context.update(doc['valores_campos'])
            elif isinstance(doc['valores_campos'], str):
                context.update(json.loads(doc['valores_campos']))
        
        # Agregar metadatos del sistema
        context['consecutivo'] = doc.get('consecutivo') or ''
        context['asunto'] = doc.get('asunto', '')
        
        # Fecha de emisión (si ya está finalizado)
        if doc.get('fecha_emision'):
            from datetime import datetime
            fecha_emision = doc['fecha_emision']
            if isinstance(fecha_emision, str):
                fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
            context['fecha_emision'] = fecha_emision.strftime('%Y-%m-%d')
            context['fecha'] = fecha_emision.strftime('%Y-%m-%d')
        else:
            # Si aún no tiene fecha, usar fecha actual como placeholder
            from datetime import datetime
            context['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        # Info del usuario que genera/aprueba (si se proporciona usuario_id)
        if usuario_id:
            datos_usuario = obtener_datos_usuario(db, usuario_id)
            context['usuario_nombre'] = datos_usuario.get('nombre', '')
            context['usuario_documento'] = datos_usuario.get('documento', '')
            context['usuario_cargo'] = datos_usuario.get('cargo', '')
            context['usuario_firma'] = datos_usuario.get('firma', '')
        else:
            # Usar datos del usuario que creó el documento
            context['usuario_nombre'] = doc.get('usuario_nombre', '')
            context['usuario_documento'] = doc.get('documento', '')
            context['usuario_cargo'] = doc.get('cargo', '')
        
        # Información general del documento
        context['tipo_documento'] = doc.get('tipo_nombre', '')
        context['plantilla_nombre'] = doc.get('plantilla_nombre', '')
        
        # Inicializar placeholders de firma vacíos (se llenarán al finalizar)
        context['unidad_nombre'] = ''
        context['unidad_cargo'] = ''
        context['unidad_firma'] = ''
        context['gerente_nombre'] = ''
        context['gerente_cargo'] = ''
        context['gerente_firma'] = ''
        
        tipo_documento = doc.get('tipo_nombre', '').upper()
        if 'RESOLUCION' in tipo_documento:
            context['juridica_nombre'] = ''
            context['juridica_cargo'] = ''
            context['juridica_firma'] = ''
        
        return context
    
    except Exception as e:
        logger.error(f"Error al generar context para plantilla: {e}")
        raise Exception(f"Error al generar context: {str(e)}")


def generar_context_con_firmas(db: Session, documento_id: int) -> dict:
    """
    Generar el context completo incluyendo firmas de aprobadores.
    Usado cuando el documento está FINALIZADO.
    
    Mapea los datos de firmas a los nombres utilizados en la plantilla y BD:
    - Rol Unidad → unidad_nombre, unidad_cargo, unidad_firma
    - Rol Jurídica → juridica_nombre, juridica_cargo, juridica_firma
    - Rol Gerencia → gerente_nombre, gerente_cargo, gerente_firma
    
    Mapeo de roles: 1=Unidad, 2=Gerencia, 3=Jurídica, 4=Otra
    
    Args:
        db: Sesión de BD
        documento_id: ID del documento
    
    Returns:
        Dict con valores_campos + metadatos + datos de firmas de los aprobadores
    """
    try:
        from app.crud.firmas_digitales import get_firmas_by_documento
        
        # Obtener contexto base del documento
        doc = get_documento_by_id(db, documento_id)
        if not doc:
            raise Exception("Documento no encontrado")
        
        context = {}
        
        # Si hay valores_campos, agregarlos al context
        if doc.get('valores_campos'):
            if isinstance(doc['valores_campos'], dict):
                context.update(doc['valores_campos'])
            elif isinstance(doc['valores_campos'], str):
                context.update(json.loads(doc['valores_campos']))
        
        # Agregar metadatos del sistema
        context['consecutivo'] = doc.get('consecutivo') or ''
        context['asunto'] = doc.get('asunto', '')
        
        # Fecha de emisión
        if doc.get('fecha_emision'):
            from datetime import datetime
            fecha_emision = doc['fecha_emision']
            if isinstance(fecha_emision, str):
                fecha_emision = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
            context['fecha_emision'] = fecha_emision.strftime('%Y-%m-%d')
            context['fecha'] = fecha_emision.strftime('%Y-%m-%d')
        else:
            from datetime import datetime
            context['fecha'] = datetime.now().strftime('%Y-%m-%d')
        
        # Información general del documento
        context['tipo_documento'] = doc.get('tipo_nombre', '')
        context['plantilla_nombre'] = doc.get('plantilla_nombre', '')
        
        # Obtener tipo de documento para determinar el flujo
        tipo_documento = doc.get('tipo_nombre', '').upper()
        requiere_juridica = 'RESOLUCION' in tipo_documento or 'RESOLUCIÓN' in tipo_documento
        
        # Agregar firmas (nombres, cargos e imágenes de aprobadores)
        # Retorna lista con id_rol para mapear por rol, no por orden
        firmas = get_firmas_by_documento(db, documento_id)
        
        # Inicializar campos vacíos por defecto
        # Nombres consistentes: {{gerente_*}}, {{unidad_*}}, {{juridica_*}}
        context['unidad_nombre'] = ''
        context['unidad_cargo'] = ''
        context['unidad_firma'] = ''
        context['juridica_nombre'] = ''
        context['juridica_cargo'] = ''
        context['juridica_firma'] = ''
        context['gerente_nombre'] = ''
        context['gerente_cargo'] = ''
        context['gerente_firma'] = ''
        
        if firmas and len(firmas) > 0:
            # Mapear firmas por rol en lugar de por orden cronológico
            # Roles esperados: 1=Unidad, 2=Gerencia, 3=Jurídica, 4=Otra
            
            usuario_por_rol = {}
            for firma in firmas:
                rol = firma.get('id_rol')
                usuario_por_rol[rol] = firma
            
            # Asignar según roles:
            # Rol 1 o 4 = Unidad (quien elabora)
            # Rol 3 = Jurídica (quien revisa)
            # Rol 2 = Gerencia (quien aprueba finalmente)
            
            if 1 in usuario_por_rol:  # Unidad
                firma_unidad = usuario_por_rol[1]
                context['unidad_nombre'] = firma_unidad.get('nombre_usuario', '')
                context['unidad_cargo'] = firma_unidad.get('cargo', '')
                context['unidad_firma'] = firma_unidad.get('firma_imagen', '') or ''
            elif 4 in usuario_por_rol:  # Otra (podría ser Subgerencia o similar)
                firma_unidad = usuario_por_rol[4]
                context['unidad_nombre'] = firma_unidad.get('nombre_usuario', '')
                context['unidad_cargo'] = firma_unidad.get('cargo', '')
                context['unidad_firma'] = firma_unidad.get('firma_imagen', '') or ''
            
            if requiere_juridica and 3 in usuario_por_rol:  # Jurídica (solo si es Resolución)
                firma_juridica = usuario_por_rol[3]
                context['juridica_nombre'] = firma_juridica.get('nombre_usuario', '')
                context['juridica_cargo'] = firma_juridica.get('cargo', '')
                context['juridica_firma'] = firma_juridica.get('firma_imagen', '') or ''
            
            if 2 in usuario_por_rol:  # Gerencia
                firma_gerente = usuario_por_rol[2]
                context['gerente_nombre'] = firma_gerente.get('nombre_usuario', '')
                context['gerente_cargo'] = firma_gerente.get('cargo', '')
                context['gerente_firma'] = firma_gerente.get('firma_imagen', '') or ''
        
        logger.info(f"Context de firmas generado para doc {documento_id}: {context}")
        return context
    
    except Exception as e:
        logger.error(f"Error al generar context con firmas: {e}")
        raise Exception(f"Error al generar context: {str(e)}")
