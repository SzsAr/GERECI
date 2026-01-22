from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException


def create_rol(db: Session, nombre: str, estado: int = 1):
    """Crear un nuevo rol con ID autoincremental"""
    try:
        query = text("""
            INSERT INTO roles (nombre, estado)
            VALUES (:nombre, :estado)
        """)
        
        result = db.execute(query, {
            'nombre': nombre,
            'estado': estado
        })
        db.commit()
        
        rol_id = result.lastrowid
        return get_rol_by_id(db, rol_id)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_rol_by_id(db: Session, rol_id: int):
    """Obtener rol por ID"""
    query = text("""
        SELECT id, nombre, estado
        FROM roles
        WHERE id = :rol_id
    """)
    
    result = db.execute(query, {'rol_id': rol_id}).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return dict(result)


def get_all_roles(db: Session, solo_activos: bool = False):
    """Obtener todos los roles"""
    if solo_activos:
        query = text("""
            SELECT id, nombre, estado
            FROM roles
            WHERE estado = 1
            ORDER BY id ASC
        """)
    else:
        query = text("""
            SELECT id, nombre, estado
            FROM roles
            ORDER BY id ASC
        """)
    
    results = db.execute(query).mappings().all()
    
    return [dict(row) for row in results]


def update_rol(db: Session, rol_id: int, nombre: str = None, estado: int = None):
    """Actualizar un rol"""
    # Verificar que el rol existe
    get_rol_by_id(db, rol_id)
    
    updates = []
    params = {'rol_id': rol_id}
    
    if nombre is not None:
        updates.append("nombre = :nombre")
        params['nombre'] = nombre
    
    if estado is not None:
        updates.append("estado = :estado")
        params['estado'] = estado
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    try:
        query = text(f"""
            UPDATE roles
            SET {', '.join(updates)}
            WHERE id = :rol_id
        """)
        
        db.execute(query, params)
        db.commit()
        
        return get_rol_by_id(db, rol_id)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def delete_rol(db: Session, rol_id: int):
    """Eliminar un rol (si no tiene usuarios asociados)"""
    # Verificar que el rol existe
    get_rol_by_id(db, rol_id)
    
    # Verificar si hay usuarios con este rol
    check_query = text("""
        SELECT COUNT(*) as count
        FROM usuarios
        WHERE id_rol = :rol_id
    """)
    
    result = db.execute(check_query, {'rol_id': rol_id}).mappings().first()
    
    if result['count'] > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el rol. Existen {result['count']} usuarios asociados"
        )
    
    try:
        query = text("""
            DELETE FROM roles
            WHERE id = :rol_id
        """)
        
        db.execute(query, {'rol_id': rol_id})
        db.commit()
        
        return {"message": "Rol eliminado exitosamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_usuarios_by_rol(db: Session, rol_id: int):
    """Obtener lista de usuarios con un rol específico"""
    # Verificar que el rol existe
    get_rol_by_id(db, rol_id)
    
    query = text("""
        SELECT id_usuario, nombre_completo, correo, estado
        FROM usuarios
        WHERE id_rol = :rol_id
        ORDER BY id_usuario ASC
    """)
    
    results = db.execute(query, {'rol_id': rol_id}).mappings().all()
    
    return [dict(row) for row in results]
