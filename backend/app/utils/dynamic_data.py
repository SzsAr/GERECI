"""
Utilidad para insertar datos en tablas dinámicas de plantillas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json
from .dynamic_tables import sanitizar_nombre_tabla

logger = logging.getLogger(__name__)


def insertar_datos_documento_en_plantilla(db: Session, id_plantilla: int, id_documento: int, 
                                         valores_campos: dict, nombre_tabla: str) -> bool:
    """
    Insertar los datos del documento en la tabla dinámica de la plantilla.
    
    Args:
        db: Sesión de BD
        id_plantilla: ID de la plantilla
        id_documento: ID del documento
        valores_campos: Dict con los valores {"nombre_campo": "valor", ...}
        nombre_tabla: Nombre de la tabla dinámica
        
    Returns:
        True si se insertó correctamente
    """
    try:
        if not nombre_tabla:
            logger.warning(f"No se encontró tabla dinámica para plantilla {id_plantilla}")
            return False
        
        # Construir columns y values (incluye columnas por defecto)
        columnas = ["id_plantilla", "id_documento", "fecha", "consecutivo"]
        placeholders = [":id_plantilla", ":id_documento", "CURRENT_TIMESTAMP", ":consecutivo"]
        params = {
            "id_plantilla": id_plantilla,
            "id_documento": id_documento,
            "consecutivo": None,
        }
        
        # Agregar campos dinámicos
        if valores_campos:
            for nombre_campo, valor in valores_campos.items():
                # Sanitizar nombre de columna y evitar columnas reservadas
                nombre_col = sanitizar_nombre_tabla(nombre_campo)
                # Ignorar campos reservados y campos de firma automáticos
                if nombre_col in {"id", "id_plantilla", "id_documento", "fecha", "consecutivo", 
                                 "campos_json", "fecha_creacion",
                                 "gerente_firma", "gerente_nombre", "gerente_cargo",
                                 "unidad_firma", "unidad_nombre", "unidad_cargo",
                                 "juridica_firma", "juridica_nombre", "juridica_cargo"}:
                    continue
                columnas.append(nombre_col)
                placeholders.append(f":{nombre_col}")
                params[nombre_col] = valor
        
        # Agregar JSON de todos los valores
        columnas.append("campos_json")
        placeholders.append(":campos_json")
        params["campos_json"] = json.dumps(valores_campos) if valores_campos else "{}"
        
        # Construir INSERT
        cols_str = ", ".join([f"`{col}`" for col in columnas])
        placeholders_str = ", ".join(placeholders)
        
        insert_sql = f"""
        INSERT INTO `{nombre_tabla}` ({cols_str})
        VALUES ({placeholders_str})
        """
        
        db.execute(text(insert_sql), params)
        db.commit()
        
        logger.info(f"Datos insertados en tabla '{nombre_tabla}' para documento {id_documento}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al insertar datos en tabla dinámica: {e}")
        raise Exception(f"Error al guardar datos del documento: {str(e)}")


def obtener_datos_documento_de_plantilla(db: Session, id_documento: int, 
                                        nombre_tabla: str) -> dict:
    """
    Obtener los datos de un documento desde su tabla dinámica.
    
    Args:
        db: Sesión de BD
        id_documento: ID del documento
        nombre_tabla: Nombre de la tabla dinámica
        
    Returns:
        Dict con los datos del documento
    """
    try:
        if not nombre_tabla:
            return {}
        
        query = text(f"""
            SELECT * FROM `{nombre_tabla}`
            WHERE id_documento = :id_documento
            LIMIT 1
        """)
        
        result = db.execute(query, {"id_documento": id_documento}).mappings().first()
        
        if result:
            data = dict(result)
            # Procesar campos_json si existe
            if data.get('campos_json') and isinstance(data['campos_json'], str):
                try:
                    data['campos_json'] = json.loads(data['campos_json'])
                except:
                    pass
            return data
        return {}
        
    except Exception as e:
        logger.error(f"Error al obtener datos de tabla dinámica: {e}")
        return {}


def actualizar_consecutivo_en_tabla_dinamica(db: Session, id_documento: int, 
                                            nombre_tabla: str, consecutivo: str) -> bool:
    """
    Actualizar el consecutivo en la tabla dinámica del documento.
    
    Args:
        db: Sesión de BD
        id_documento: ID del documento
        nombre_tabla: Nombre de la tabla dinámica
        consecutivo: Consecutivo asignado
        
    Returns:
        True si se actualizó correctamente
    """
    try:
        if not nombre_tabla:
            logger.warning(f"No se encontró tabla dinámica para actualizar consecutivo del documento {id_documento}")
            return False
        
        update_sql = f"""
        UPDATE `{nombre_tabla}`
        SET consecutivo = :consecutivo
        WHERE id_documento = :id_documento
        """
        
        db.execute(text(update_sql), {
            "consecutivo": consecutivo,
            "id_documento": id_documento
        })
        db.commit()
        
        logger.info(f"Consecutivo '{consecutivo}' actualizado en tabla '{nombre_tabla}' para documento {id_documento}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar consecutivo en tabla dinámica: {e}")
        return False


def actualizar_firmas_en_tabla_dinamica(db: Session, id_documento: int, 
                                        nombre_tabla: str, context_firmas: dict) -> bool:
    """
    Actualizar los campos de firmas, nombres y cargos en la tabla dinámica del documento.
    
    Mapea desde el context (que usa nombres: gerente_*, unidad_*, juridica_*) 
    a columnas en la tabla dinámica (que también usan los mismos nombres).
    
    Args:
        db: Sesión de BD
        id_documento: ID del documento
        nombre_tabla: Nombre de la tabla dinámica
        context_firmas: Dict con los datos generados por generar_context_con_firmas()
                       Incluye: gerente_nombre, gerente_cargo, gerente_firma,
                                unidad_nombre, unidad_cargo, unidad_firma,
                                juridica_nombre, juridica_cargo, juridica_firma
        
    Returns:
        True si se actualizó correctamente
    """
    try:
        if not nombre_tabla:
            logger.warning(f"No se encontró tabla dinámica para actualizar firmas del documento {id_documento}")
            return False
        
        # Mapear campos que queremos actualizar en la tabla dinámica
        # Los nombres ya vienen correctos desde generar_context_con_firmas()
        campos_a_actualizar = {}
        
        # Campos de unidad (quien elabora)
        if 'unidad_nombre' in context_firmas and context_firmas['unidad_nombre']:
            campos_a_actualizar['unidad_nombre'] = context_firmas['unidad_nombre']
        if 'unidad_cargo' in context_firmas and context_firmas['unidad_cargo']:
            campos_a_actualizar['unidad_cargo'] = context_firmas['unidad_cargo']
        if 'unidad_firma' in context_firmas and context_firmas['unidad_firma']:
            campos_a_actualizar['unidad_firma'] = context_firmas['unidad_firma']
        
        # Campos de jurídica (si existen)
        if 'juridica_nombre' in context_firmas and context_firmas['juridica_nombre']:
            campos_a_actualizar['juridica_nombre'] = context_firmas['juridica_nombre']
        if 'juridica_cargo' in context_firmas and context_firmas['juridica_cargo']:
            campos_a_actualizar['juridica_cargo'] = context_firmas['juridica_cargo']
        if 'juridica_firma' in context_firmas and context_firmas['juridica_firma']:
            campos_a_actualizar['juridica_firma'] = context_firmas['juridica_firma']
        
        # Campos de gerente
        if 'gerente_nombre' in context_firmas and context_firmas['gerente_nombre']:
            campos_a_actualizar['gerente_nombre'] = context_firmas['gerente_nombre']
        if 'gerente_cargo' in context_firmas and context_firmas['gerente_cargo']:
            campos_a_actualizar['gerente_cargo'] = context_firmas['gerente_cargo']
        if 'gerente_firma' in context_firmas and context_firmas['gerente_firma']:
            campos_a_actualizar['gerente_firma'] = context_firmas['gerente_firma']
        
        if not campos_a_actualizar:
            logger.info(f"No hay campos de firma para actualizar en documento {id_documento}")
            return True
        
        # Construir SET dinámicamente
        set_clauses = []
        params = {"id_documento": id_documento}
        
        for col, val in campos_a_actualizar.items():
            set_clauses.append(f"`{col}` = :{col}")
            params[col] = val
        
        set_str = ", ".join(set_clauses)
        
        update_sql = f"""
        UPDATE `{nombre_tabla}`
        SET {set_str}
        WHERE id_documento = :id_documento
        """
        
        result = db.execute(text(update_sql), params)
        db.commit()
        
        logger.info(f"Firmas actualizadas en tabla '{nombre_tabla}' para documento {id_documento}: {campos_a_actualizar}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar firmas en tabla dinámica: {e}")
        return False
