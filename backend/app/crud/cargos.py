from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException


def create_cargo(db: Session, nombre: str, descripcion: str = None, estado: int = 1):
    """Crear un nuevo cargo"""
    try:
        query = text("""
            INSERT INTO cargos (nombre, descripcion, estado)
            VALUES (:nombre, :descripcion, :estado)
        """)
        
        result = db.execute(query, {
            'nombre': nombre,
            'descripcion': descripcion,
            'estado': estado
        })
        db.commit()
        
        cargo_id = result.lastrowid
        return get_cargo_by_id(db, cargo_id)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_cargo_by_id(db: Session, cargo_id: int):
    """Obtener cargo por ID"""
    query = text("""
        SELECT id, nombre, descripcion, estado
        FROM cargos
        WHERE id = :cargo_id
    """)
    
    result = db.execute(query, {'cargo_id': cargo_id}).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    
    return dict(result)


def get_all_cargos(db: Session, solo_activos: bool = False):
    """Obtener todos los cargos"""
    if solo_activos:
        query = text("""
            SELECT id, nombre, descripcion, estado
            FROM cargos
            WHERE estado = 1
            ORDER BY id ASC
        """)
    else:
        query = text("""
            SELECT id, nombre, descripcion, estado
            FROM cargos
            ORDER BY id ASC
        """)
    
    results = db.execute(query).mappings().all()
    
    return [dict(row) for row in results]


def update_cargo(db: Session, cargo_id: int, nombre: str = None, descripcion: str = None, estado: int = None):
    """Actualizar un cargo"""
    # Verificar que el cargo existe
    get_cargo_by_id(db, cargo_id)
    
    updates = []
    params = {'cargo_id': cargo_id}
    
    if nombre is not None:
        updates.append("nombre = :nombre")
        params['nombre'] = nombre
    
    if descripcion is not None:
        updates.append("descripcion = :descripcion")
        params['descripcion'] = descripcion
    
    if estado is not None:
        updates.append("estado = :estado")
        params['estado'] = estado
    
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    try:
        query = text(f"""
            UPDATE cargos
            SET {', '.join(updates)}
            WHERE id = :cargo_id
        """)
        
        db.execute(query, params)
        db.commit()
        
        return get_cargo_by_id(db, cargo_id)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def delete_cargo(db: Session, cargo_id: int):
    """Eliminar un cargo (si no tiene usuarios asociados)"""
    # Verificar que el cargo existe
    get_cargo_by_id(db, cargo_id)
    
    # Verificar si hay usuarios con este cargo
    check_query = text("""
        SELECT COUNT(*) as count
        FROM usuarios
        WHERE id_cargo = :cargo_id
    """)
    
    result = db.execute(check_query, {'cargo_id': cargo_id}).mappings().first()
    
    if result['count'] > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el cargo. Existen {result['count']} usuarios asociados"
        )
    
    try:
        query = text("""
            DELETE FROM cargos
            WHERE id = :cargo_id
        """)
        
        db.execute(query, {'cargo_id': cargo_id})
        db.commit()
        
        return {"message": "Cargo eliminado exitosamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def get_usuarios_by_cargo(db: Session, cargo_id: int):
    """Obtener lista de usuarios con un cargo específico"""
    # Verificar que el cargo existe
    get_cargo_by_id(db, cargo_id)
    
    query = text("""
        SELECT u.id as id_usuario, u.nombre as nombre_completo, 
               u.documento, u.username, u.estado,
               r.nombre as rol
        FROM usuarios u
        LEFT JOIN roles r ON u.id_rol = r.id
        WHERE u.id_cargo = :cargo_id
        ORDER BY u.id ASC
    """)
    
    results = db.execute(query, {'cargo_id': cargo_id}).mappings().all()
    
    return [dict(row) for row in results]
