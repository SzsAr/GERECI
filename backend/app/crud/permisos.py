"""
CRUD operations for permissions management
"""
from sqlalchemy.orm import Session
from sqlalchemy import text


def verify_permissions(db: Session, id_rol: int, id_modulo: int, accion: str) -> bool:
    """
    Verificar si un rol tiene permiso para realizar una acción en un módulo.
    
    Args:
        db: Sesión de base de datos
        id_rol: ID del rol del usuario
        id_modulo: ID del módulo
        accion: Tipo de acción ('insertar', 'actualizar', 'seleccionar', 'borrar')
    
    Returns:
        bool: True si tiene permiso, False si no
    """
    
    if accion not in ['insertar', 'actualizar', 'seleccionar', 'borrar']:
        return False
    
    try:
        # Consultar los permisos de la base de datos
        query = text("""
            SELECT * FROM permisos 
            WHERE id_modulo = :id_modulo AND id_rol = :id_rol
        """)
        
        result = db.execute(query, {"id_modulo": id_modulo, "id_rol": id_rol}).fetchone()
        
        if result is None:
            return False
        
        # Obtener el valor del permiso según la acción
        if accion == 'insertar':
            return result.insertar
        elif accion == 'actualizar':
            return result.actualizar
        elif accion == 'seleccionar':
            return result.seleccionar
        elif accion == 'borrar':
            return result.borrar
        
        return False
    
    except Exception as e:
        print(f"Error verificando permisos: {str(e)}")
        return False


def get_all_permissions(db: Session, id_rol: int) -> dict:
    """
    Obtener todos los permisos de un rol
    
    Args:
        db: Sesión de base de datos
        id_rol: ID del rol
    
    Returns:
        dict: Diccionario con los permisos por módulo
    """
    try:
        query = text("""
            SELECT id_modulo, insertar, actualizar, seleccionar, borrar 
            FROM permisos 
            WHERE id_rol = :id_rol
        """)
        
        results = db.execute(query, {"id_rol": id_rol}).fetchall()
        
        permissions = {}
        for row in results:
            permissions[row.id_modulo] = {
                'insertar': row.insertar,
                'actualizar': row.actualizar,
                'seleccionar': row.seleccionar,
                'borrar': row.borrar
            }
        
        return permissions
    
    except Exception as e:
        print(f"Error obteniendo permisos: {str(e)}")
        return {}
