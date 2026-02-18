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
                                 "firma_gerente", "nombre_gerente", "cargo_gerente",
                                 "firma_elabora", "nombre_elabora", "cargo_elabora",
                                 "firma_revisa", "nombre_revisa", "cargo_revisa"}:
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
