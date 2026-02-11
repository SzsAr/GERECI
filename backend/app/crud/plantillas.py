"""
CRUD operations for plantillas - Generador de tablas dinámicas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging
import json
from collections import OrderedDict
import uuid
from pathlib import Path

from app.utils.dynamic_tables import crear_tabla_dinamica_plantilla, eliminar_tabla_dinamica_plantilla

logger = logging.getLogger(__name__)

# Directorio para almacenar plantillas
PLANTILLAS_DIR = Path(__file__).parent.parent.parent / "media" / "plantillas"
PLANTILLAS_DIR.mkdir(parents=True, exist_ok=True)


def create_plantilla(db: Session, id_tipo: int, nombre: str, campos_json: dict, 
                     descripcion: Optional[str] = None) -> Optional[int]:
    """
    Crear una plantilla y su tabla dinámmica asociada.
    
    Los campos de firma NO se incluyen en campos_json (no aparecen en modal).
    Se crean automáticamente como columnas en la tabla dinámica según el tipo:
    - RESOLUCIÓN: firma_gerente, nombre_gerente, cargo_gerente, firma_elabora,
      nombre_elabora, cargo_elabora, firma_revisa, nombre_revisa, cargo_revisa
    - CIRCULAR: firma_gerente, nombre_gerente, cargo_gerente, firma_elabora,
      nombre_elabora, cargo_elabora
    
    Args:
        db: Sesión de BD
        id_tipo: ID del tipo de documento
        nombre: Nombre de la plantilla (se usará como base para el nombre de la tabla)
        campos_json: Dict con los campos {"nombre": "tipo_dato", ...}
        descripcion: Descripción opcional (no se usa actualmente en BD)
    
    Returns:
        ID de la plantilla creada
    """
    try:
        # Obtener tipo de documento para pasarlo a crear_tabla_dinamica_plantilla
        tipo_query = text("SELECT nombre FROM tipos_documentos WHERE id = :id_tipo")
        tipo_result = db.execute(tipo_query, {"id_tipo": id_tipo}).fetchone()
        tipo_nombre = tipo_result[0] if tipo_result else ""
        
        # NO agregar campos de firma al JSON (solo campos del usuario)
        campos_usuario = dict(campos_json) if isinstance(campos_json, dict) else {}
        
        # Serializar solo los campos del usuario (sin campos de firma)
        campos_serializados = json.dumps(campos_usuario) if isinstance(campos_usuario, dict) else campos_usuario
        
        # Insertar plantilla
        query = text("""
            INSERT INTO plantillas (id_tipo, nombre, campos_json, descripcion, estado)
            VALUES (:id_tipo, :nombre, :campos_json, :descripcion, 1)
        """)
        result = db.execute(query, {
            "id_tipo": id_tipo,
            "nombre": nombre,
            "campos_json": campos_serializados,
            "descripcion": descripcion
        })
        db.commit()
        
        plantilla_id = result.lastrowid
        
        # Crear tabla dinámica para la plantilla (pasando tipo de documento)
        crear_tabla_dinamica_plantilla(db, plantilla_id, nombre, campos_usuario, tipo_nombre)
        
        logger.info(f"Plantilla '{nombre}' creada con ID {plantilla_id}")
        return plantilla_id
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear plantilla: {e}")
        raise Exception(f"Error de base de datos al crear plantilla: {str(e)}")


def get_plantilla_by_id(db: Session, plantilla_id: int):
    """Obtener una plantilla por ID con su información de tipo y tabla dinámica"""
    try:
        query = text("""
            SELECT p.id, p.id_tipo, p.nombre, p.campos_json,
                   p.descripcion, p.estado, p.fecha_creacion,
                   p.nombre_archivo, p.ruta_almacenamiento,
                   t.nombre AS tipo_nombre,
                   pt.nombre_tabla
            FROM plantillas p
            LEFT JOIN tipos_documentos t ON p.id_tipo = t.id
            LEFT JOIN plantillas_tablas_dinamicas pt ON p.id = pt.id_plantilla
            WHERE p.id = :id
        """)
        result = db.execute(query, {"id": plantilla_id}).mappings().first()
        
        if result:
            result_dict = dict(result)
            
            # Obtener orden de columnas desde la tabla dinámica de BD
            if result_dict.get('nombre_tabla'):
                campos_ordenados = obtener_campos_ordenados_desde_tabla(db, result_dict['nombre_tabla'])
                if campos_ordenados:
                    result_dict['campos_json'] = campos_ordenados
                elif result_dict.get("campos_json") and isinstance(result_dict["campos_json"], str):
                    try:
                        result_dict["campos_json"] = json.loads(result_dict["campos_json"], object_pairs_hook=OrderedDict)
                    except json.JSONDecodeError:
                        pass
            elif result_dict.get("campos_json") and isinstance(result_dict["campos_json"], str):
                try:
                    result_dict["campos_json"] = json.loads(result_dict["campos_json"], object_pairs_hook=OrderedDict)
                except json.JSONDecodeError:
                    pass
            
            return result_dict
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener plantilla: {e}")
        raise Exception("Error de base de datos al obtener plantilla")


def get_all_plantillas(db: Session) -> List:
    """Obtener todas las plantillas activas con sus tablas dinámicas"""
    try:
        query = text("""
            SELECT p.id, p.id_tipo, p.nombre, p.campos_json,
                   p.descripcion, p.estado, p.fecha_creacion,
                   p.nombre_archivo, p.ruta_almacenamiento,
                   t.nombre AS tipo_nombre,
                   pt.nombre_tabla
            FROM plantillas p
            LEFT JOIN tipos_documentos t ON p.id_tipo = t.id
            LEFT JOIN plantillas_tablas_dinamicas pt ON p.id = pt.id_plantilla
            WHERE p.estado = 1
            ORDER BY p.id DESC
        """)
        result = db.execute(query).mappings().all()
        
        parsed = []
        for row in result:
            row_dict = dict(row)
            
            # Obtener orden de columnas desde la tabla dinámica de BD
            if row_dict.get('nombre_tabla'):
                campos_ordenados = obtener_campos_ordenados_desde_tabla(db, row_dict['nombre_tabla'])
                if campos_ordenados:
                    row_dict['campos_json'] = campos_ordenados
                elif row_dict.get("campos_json") and isinstance(row_dict["campos_json"], str):
                    # Fallback: deserializar del JSON si no se pudo obtener de la tabla
                    try:
                        row_dict["campos_json"] = json.loads(row_dict["campos_json"], object_pairs_hook=OrderedDict)
                    except json.JSONDecodeError:
                        pass
            elif row_dict.get("campos_json") and isinstance(row_dict["campos_json"], str):
                # Deserializar campos_json preservando orden de inserción
                try:
                    row_dict["campos_json"] = json.loads(row_dict["campos_json"], object_pairs_hook=OrderedDict)
                except json.JSONDecodeError:
                    pass
            
            parsed.append(row_dict)
        return parsed
        
    except Exception as e:
        logger.error(f"Error al obtener plantillas: {e}")
        raise Exception("Error de base de datos al obtener plantillas")


def obtener_campos_ordenados_desde_tabla(db: Session, nombre_tabla: str) -> Optional[OrderedDict]:
    """
    Obtener campos de una tabla dinámica en el orden en que fueron creados (ORDINAL_POSITION).
    Excluye columnas de sistema/control y campos de firma (no se muestran en modal).
    """
    try:
        # Columnas que no son campos dinámicos (incluye campos de firma automáticos)
        columnas_excluidas = {'id', 'id_plantilla', 'id_documento', 'campos_json', 
                             'fecha', 'consecutivo', 'fecha_creacion',
                             'firma_gerente', 'nombre_gerente', 'cargo_gerente',
                             'firma_elabora', 'nombre_elabora', 'cargo_elabora',
                             'firma_revisa', 'nombre_revisa', 'cargo_revisa'}
        
        query = text("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :tabla
              AND COLUMN_NAME NOT IN ('id', 'id_plantilla', 'id_documento', 
                                      'campos_json', 'fecha', 'consecutivo', 'fecha_creacion',
                                      'firma_gerente', 'nombre_gerente', 'cargo_gerente',
                                      'firma_elabora', 'nombre_elabora', 'cargo_elabora',
                                      'firma_revisa', 'nombre_revisa', 'cargo_revisa')
            ORDER BY ORDINAL_POSITION
        """)
        
        result = db.execute(query, {"tabla": nombre_tabla}).mappings().all()
        
        if not result:
            return None
        
        # Crear OrderedDict con el orden de la BD
        campos = OrderedDict()
        for row in result:
            col_name = row['COLUMN_NAME']
            data_type = row['DATA_TYPE']
            
            # Mapear tipos de MySQL a nuestros tipos
            tipo_mapeado = mapear_tipo_mysql_a_app(data_type)
            campos[col_name] = tipo_mapeado
        
        return campos if campos else None
        
    except Exception as e:
        logger.error(f"Error al obtener campos ordenados de tabla {nombre_tabla}: {e}")
        return None


def mapear_tipo_mysql_a_app(tipo_mysql: str) -> str:
    """Mapear tipos de datos de MySQL a los tipos de la aplicación"""
    mapeo = {
        'varchar': 'varchar',
        'text': 'text',
        'int': 'int',
        'tinyint': 'int',
        'smallint': 'int',
        'mediumint': 'int',
        'bigint': 'int',
        'float': 'float',
        'double': 'float',
        'decimal': 'decimal',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'boolean': 'boolean',
        'tinyint(1)': 'boolean'
    }
    return mapeo.get(tipo_mysql.lower(), 'varchar')


def get_plantillas_by_tipo(db: Session, id_tipo: int) -> List:
    """Obtener todas las plantillas de un tipo de documento"""
    try:
        query = text("""
            SELECT p.id, p.id_tipo, p.nombre, p.campos_json,
                   p.descripcion, p.estado, p.fecha_creacion,
                   p.nombre_archivo, p.ruta_almacenamiento,
                   t.nombre AS tipo_nombre,
                   pt.nombre_tabla
            FROM plantillas p
            LEFT JOIN tipos_documentos t ON p.id_tipo = t.id
            LEFT JOIN plantillas_tablas_dinamicas pt ON p.id = pt.id_plantilla
            WHERE p.id_tipo = :id_tipo AND p.estado = 1
            ORDER BY p.nombre ASC
        """)
        result = db.execute(query, {"id_tipo": id_tipo}).mappings().all()
        
        parsed = []
        for row in result:
            row_dict = dict(row)
            
            # Obtener orden de columnas desde la tabla dinámica de BD
            if row_dict.get('nombre_tabla'):
                campos_ordenados = obtener_campos_ordenados_desde_tabla(db, row_dict['nombre_tabla'])
                if campos_ordenados:
                    row_dict['campos_json'] = campos_ordenados
                elif row_dict.get("campos_json") and isinstance(row_dict["campos_json"], str):
                    try:
                        row_dict["campos_json"] = json.loads(row_dict["campos_json"], object_pairs_hook=OrderedDict)
                    except json.JSONDecodeError:
                        pass
            elif row_dict.get("campos_json") and isinstance(row_dict["campos_json"], str):
                try:
                    row_dict["campos_json"] = json.loads(row_dict["campos_json"], object_pairs_hook=OrderedDict)
                except json.JSONDecodeError:
                    pass
            
            parsed.append(row_dict)
        return parsed
        
    except Exception as e:
        logger.error(f"Error al obtener plantillas por tipo: {e}")
        return []


def update_plantilla(db: Session, plantilla_id: int, 
                     nombre: Optional[str] = None,
                     descripcion: Optional[str] = None,
                     estado: Optional[int] = None) -> bool:
    """
    Actualizar datos de la plantilla (NO se pueden cambiar campos_json ni id_tipo)
    """
    try:
        updates = {}
        
        if nombre is not None:
            updates["nombre"] = nombre
        if descripcion is not None:
            updates["descripcion"] = descripcion
        if estado is not None:
            updates["estado"] = estado
        
        if not updates:
            return False
        
        set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
        updates["id"] = plantilla_id
        
        query = text(f"UPDATE plantillas SET {set_clause} WHERE id = :id")
        result = db.execute(query, updates)
        db.commit()
        
        logger.info(f"Plantilla {plantilla_id} actualizada")
        return result.rowcount > 0
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar plantilla: {e}")
        raise Exception(f"Error al actualizar plantilla: {str(e)}")


def delete_plantilla(db: Session, plantilla_id: int) -> bool:
    """
    Eliminar una plantilla y su tabla dinámica asociada.
    No se puede eliminar si existen documentos que la usan.
    """
    try:
        # Verificar si hay documentos usando esta plantilla
        check_query = text("""
            SELECT COUNT(*) as count FROM documentos WHERE id_plantilla = :id_plantilla
        """)
        result = db.execute(check_query, {"id_plantilla": plantilla_id}).fetchone()
        
        if result and result[0] > 0:
            raise Exception(f"No se puede eliminar la plantilla. Hay {result[0]} documento(s) que la usan")
        
        # Eliminar tabla dinámmica
        eliminar_tabla_dinamica_plantilla(db, plantilla_id)
        
        # Eliminar plantilla
        query = text("DELETE FROM plantillas WHERE id = :id")
        result = db.execute(query, {"id": plantilla_id})
        db.commit()
        
        logger.info(f"Plantilla {plantilla_id} eliminada")
        return result.rowcount > 0
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar plantilla: {e}")
        raise Exception(f"Error al eliminar plantilla: {str(e)}")


def guardar_archivo_plantilla(db: Session, plantilla_id: int, archivo_bytes: bytes, 
                               nombre_original: str) -> dict:
    """
    Guardar archivo .docx de plantilla y actualizar registro en BD.
    
    Args:
        db: Sesión de BD
        plantilla_id: ID de la plantilla
        archivo_bytes: Contenido del archivo .docx
        nombre_original: Nombre original del archivo subido
    
    Returns:
        Dict con nombre_archivo y ruta_almacenamiento
    """
    try:
        # Verificar que la plantilla existe
        plantilla = get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise Exception("Plantilla no encontrada")
        
        # Validar extensión
        if not nombre_original.lower().endswith('.docx'):
            raise ValueError("El archivo debe ser .docx")
        
        # Generar nombre único para el archivo
        uuid_nombre = f"{uuid.uuid4()}.docx"
        ruta_fisica = PLANTILLAS_DIR / uuid_nombre
        
        # Guardar archivo físicamente
        with open(ruta_fisica, 'wb') as f:
            f.write(archivo_bytes)
        
        # Ruta relativa para servir desde /static
        ruta_almacenamiento = f"/static/plantillas/{uuid_nombre}"
        
        # Actualizar registro en BD
        query = text("""
            UPDATE plantillas 
            SET nombre_archivo = :nombre_archivo, 
                ruta_almacenamiento = :ruta_almacenamiento
            WHERE id = :id
        """)
        
        db.execute(query, {
            "nombre_archivo": nombre_original,
            "ruta_almacenamiento": ruta_almacenamiento,
            "id": plantilla_id
        })
        db.commit()
        
        logger.info(f"Archivo de plantilla guardado: {nombre_original} -> {uuid_nombre}")
        
        return {
            "nombre_archivo": nombre_original,
            "ruta_almacenamiento": ruta_almacenamiento,
            "ruta_fisica": str(ruta_fisica)
        }
    
    except ValueError as e:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar archivo de plantilla: {e}")
        raise Exception(f"Error al guardar archivo: {str(e)}")


def extraer_placeholders_de_plantilla(plantilla_id: int, db: Session) -> dict:
    """
    Extraer placeholders (variables Jinja2) de un archivo de plantilla .docx.
    Útil para que el usuario vea qué variables debe proporcionar.
    
    Returns:
        Dict con lista de variables encontradas
    """
    try:
        from docxtpl import DocxTemplate
        import re
        
        # Obtener plantilla
        plantilla = get_plantilla_by_id(db, plantilla_id)
        if not plantilla:
            raise Exception("Plantilla no encontrada")
        
        # Verificar que tiene archivo
        ruta_almacenamiento = plantilla.get('ruta_almacenamiento')
        nombre_archivo = plantilla.get('nombre_archivo')
        
        if not ruta_almacenamiento:
            raise Exception("La plantilla no tiene archivo asociado")
        
        # Construir ruta física
        if ruta_almacenamiento.startswith('/static/'):
            archivo_relativo = ruta_almacenamiento.replace('/static/plantillas/', '')
            ruta_fisica = PLANTILLAS_DIR / archivo_relativo
        else:
            ruta_fisica = Path(ruta_almacenamiento)
        
        if not ruta_fisica.exists():
            raise Exception(f"Archivo de plantilla no encontrado: {ruta_fisica}")
        
        # Cargar plantilla y extraer texto XML
        doc_template = DocxTemplate(str(ruta_fisica))
        xml_content = doc_template.get_xml()
        
        # Buscar variables {{ variable }}
        variables_simples = set(re.findall(r'\{\{\s*(\w+(?:\.\w+)*)\s*\}\}', xml_content))
        
        # Buscar bucles {% for variable in lista %}
        bucles_for = set(re.findall(r'\{%\s*for\s+\w+\s+in\s+(\w+)\s*%\}', xml_content))
        
        # Buscar condicionales {% if variable %}
        condicionales = set(re.findall(r'\{%\s*if\s+(\w+)', xml_content))
        
        return {
            "variables_encontradas": sorted(list(variables_simples)),
            "listas_bucles": sorted(list(bucles_for)),
            "condicionales": sorted(list(condicionales)),
            "total_placeholders": len(variables_simples) + len(bucles_for) + len(condicionales)
        }
    
    except Exception as e:
        logger.error(f"Error al extraer placeholders: {e}")
        raise Exception(f"Error al analizar plantilla: {str(e)}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar plantilla: {e}")
        raise Exception(f"Error al eliminar plantilla: {str(e)}")
