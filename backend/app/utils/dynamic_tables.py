"""
Utilidad para crear tablas dinámicas de plantillas
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import json
import re

logger = logging.getLogger(__name__)

# Mapeo de tipos de datos admitidos
TIPOS_DATOS_PERMITIDOS = {
    'varchar': 'VARCHAR(255)',
    'text': 'TEXT',
    'int': 'INT',
    'float': 'FLOAT',
    'date': 'DATE',
    'datetime': 'DATETIME',
    'decimal': 'DECIMAL(10, 2)',
    'boolean': 'BOOLEAN'
}

# Columnas reservadas que no pueden usarse como nombres de campos
RESERVED_COLUMNS = {
    'id', 'id_plantilla', 'id_documento', 'campos_json',
    'fecha', 'consecutivo', 'fecha_creacion',
    'firma_gerente', 'nombre_gerente', 'cargo_gerente',
    'firma_elabora', 'nombre_elabora', 'cargo_elabora',
    'firma_revisa', 'nombre_revisa', 'cargo_revisa'
}

def sanitizar_nombre_tabla(nombre: str) -> str:
    """
    Sanitizar nombre de tabla (sin espacios, caracteres especiales, etc.)
    """
    # Convertir a minúsculas, reemplazar espacios por underscore
    nombre = nombre.lower().strip()
    # Remover caracteres especiales
    nombre = re.sub(r'[^a-z0-9_]', '_', nombre)
    # No puede empezar con número
    if nombre[0].isdigit():
        nombre = f"tabla_{nombre}"
    # Máximo 64 caracteres (límite de MySQL)
    nombre = nombre[:64]
    return nombre


def crear_tabla_dinamica_plantilla(db: Session, id_plantilla: int, nombre_plantilla: str, 
                                    campos_json: dict, tipo_documento: str = "") -> bool:
    """
    Crear tabla dinámicamente para una plantilla.
    
    Estructura esperada en campos_json:
    {
        "nombre_campo": "varchar",  (o int, text, date, etc.)
        "otro_campo": "int",
        ...
    }
    
    Automáticamente agrega columnas de firma según el tipo de documento:
    - RESOLUCIÓN: firma_gerente, nombre_gerente, cargo_gerente, firma_elabora,
      nombre_elabora, cargo_elabora, firma_revisa, nombre_revisa, cargo_revisa
    - CIRCULAR: firma_gerente, nombre_gerente, cargo_gerente, firma_elabora,
      nombre_elabora, cargo_elabora
    
    La tabla tendrá columnas:
    - id_plantilla (FK)
    - id_documento (FK a documentos)
    - campos dinámicos del usuario
    - campos de firma automáticos (según tipo)
    - campos_json (para guardar el JSON también)
    - fecha_creacion
    """
    try:
        nombre_tabla = sanitizar_nombre_tabla(nombre_plantilla)
        
        # Construir definición de columnas
        columnas = [
            "`id_plantilla` TINYINT NOT NULL COMMENT 'Referencia a plantilla'",
            "`id_documento` INT NOT NULL UNIQUE COMMENT 'Referencia a documento (FK)'",
        ]
        
        # Validar y agregar campos dinámicos
        for nombre_campo, tipo_dato in campos_json.items():
            # Validar que el tipo esté permitido
            tipo_sql = TIPOS_DATOS_PERMITIDOS.get(tipo_dato.lower(), 'VARCHAR(255)')
            
            # Sanitizar nombre de columna
            nombre_col = sanitizar_nombre_tabla(nombre_campo)
            if nombre_col in RESERVED_COLUMNS:
                nombre_col = f"campo_{nombre_col}"
            
            columnas.append(f"`{nombre_col}` {tipo_sql}")
        
        # Agregar columnas de firma según el tipo de documento
        tipo_upper = tipo_documento.upper()
        
        # Para todos los tipos con firmas: agregar elabora y gerente
        if any(tipo in tipo_upper for tipo in ['RESOLUCION', 'CIRCULAR']):
            columnas.append("`firma_elabora` TEXT NULL COMMENT 'Ruta de firma de quien elabora'")
            columnas.append("`nombre_elabora` VARCHAR(255) NULL COMMENT 'Nombre de quien elabora'")
            columnas.append("`cargo_elabora` VARCHAR(255) NULL COMMENT 'Cargo de quien elabora'")
            
            columnas.append("`firma_gerente` TEXT NULL COMMENT 'Ruta de firma del gerente'")
            columnas.append("`nombre_gerente` VARCHAR(255) NULL COMMENT 'Nombre del gerente'")
            columnas.append("`cargo_gerente` VARCHAR(255) NULL COMMENT 'Cargo del gerente'")
        
        # Solo para RESOLUCIÓN: agregar quien revisa
        if 'RESOLUCION' in tipo_upper:
            columnas.append("`firma_revisa` TEXT NULL COMMENT 'Ruta de firma de quien revisa'")
            columnas.append("`nombre_revisa` VARCHAR(255) NULL COMMENT 'Nombre de quien revisa'")
            columnas.append("`cargo_revisa` VARCHAR(255) NULL COMMENT 'Cargo de quien revisa'")
        
        # Agregar columnas por defecto para control del documento
        columnas.append("`fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha del documento (automática)'")
        columnas.append("`consecutivo` VARCHAR(50) NULL COMMENT 'Consecutivo asignado al documento'")

        # Agregar columnas de auditoría
        columnas.append("`campos_json` JSON COMMENT 'JSON con todos los valores'")
        columnas.append("`fecha_creacion` DATETIME DEFAULT CURRENT_TIMESTAMP")
        
        # Construir y ejecutar CREATE TABLE
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{nombre_tabla}` (
            `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            {', '.join(columnas)},
            KEY `idx_id_plantilla` (`id_plantilla`),
            KEY `idx_id_documento` (`id_documento`),
            KEY `idx_consecutivo` (`consecutivo`),
            CONSTRAINT `fk_{nombre_tabla}_documento` 
                FOREIGN KEY (`id_documento`) 
                REFERENCES `documentos` (`id`) 
                ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 
        COLLATE=utf8mb4_0900_ai_ci 
        COMMENT='Tabla dinámica generada para plantilla: {nombre_plantilla}'
        """
        
        db.execute(text(create_table_sql))
        
        # Registrar en tabla de control
        control_insert = text("""
            INSERT INTO plantillas_tablas_dinamicas (id_plantilla, nombre_tabla)
            VALUES (:id_plantilla, :nombre_tabla)
        """)
        db.execute(control_insert, {
            "id_plantilla": id_plantilla,
            "nombre_tabla": nombre_tabla
        })
        
        db.commit()
        logger.info(f"Tabla dinámica '{nombre_tabla}' creada exitosamente para plantilla ID {id_plantilla}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear tabla dinámica: {e}")
        raise Exception(f"Error al crear tabla de plantilla: {str(e)}")


def obtener_nombre_tabla_plantilla(db: Session, id_plantilla: int) -> str:
    """
    Obtener el nombre de tabla dinámmica asociada a una plantilla
    """
    try:
        query = text("""
            SELECT nombre_tabla FROM plantillas_tablas_dinamicas 
            WHERE id_plantilla = :id_plantilla
            LIMIT 1
        """)
        result = db.execute(query, {"id_plantilla": id_plantilla}).scalar()
        return result
    except Exception as e:
        logger.error(f"Error al obtener nombre de tabla: {e}")
        return None


def eliminar_tabla_dinamica_plantilla(db: Session, id_plantilla: int) -> bool:
    """
    Eliminar tabla dinámica de una plantilla
    """
    try:
        nombre_tabla = obtener_nombre_tabla_plantilla(db, id_plantilla)
        
        if not nombre_tabla:
            return False
        
        # Eliminar la tabla
        db.execute(text(f"DROP TABLE IF EXISTS `{nombre_tabla}`"))
        
        # Eliminar registro de control
        db.execute(text("""
            DELETE FROM plantillas_tablas_dinamicas 
            WHERE id_plantilla = :id_plantilla
        """), {"id_plantilla": id_plantilla})
        
        db.commit()
        logger.info(f"Tabla dinámica '{nombre_tabla}' eliminada")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar tabla dinámica: {e}")
        return False
