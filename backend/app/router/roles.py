from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Annotated

from app.schemas.roles import RolCreate, RolUpdate, RolOut
from app.schemas.users import UserOut
from app.crud import roles as crud_roles
from app.api.dependencies import get_db, get_current_user
from app.crud.permisos import verify_permissions


router = APIRouter()

# ID del módulo Roles en la tabla modulos
modulo = 3


@router.post("/", response_model=RolOut, status_code=status.HTTP_201_CREATED)
def create_rol(
    rol: RolCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear un nuevo rol.
    Requiere permiso de insertar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear roles'
            )
        
        nuevo_rol = crud_roles.create_rol(
            db,
            nombre=rol.nombre, 
            estado=rol.estado
        )
        
        return nuevo_rol
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RolOut], status_code=status.HTTP_200_OK)
def get_roles(
    solo_activos: bool = False,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todos los roles.
    Si solo_activos=True, solo devuelve roles con estado=1.
    Requiere permiso de seleccionar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver roles'
            )
        
        roles = crud_roles.get_all_roles(db, solo_activos)
        
        return roles
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rol_id}", response_model=RolOut, status_code=status.HTTP_200_OK)
def get_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener un rol por ID.
    Requiere permiso de seleccionar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver roles'
            )
        
        rol = crud_roles.get_rol_by_id(db, rol_id)
        
        return rol
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{rol_id}", response_model=RolOut, status_code=status.HTTP_200_OK)
def update_rol(
    rol_id: int,
    rol: RolUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Actualizar un rol.
    Requiere permiso de actualizar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar roles'
            )
        
        rol_actualizado = crud_roles.update_rol(
            db, 
            rol_id, 
            nombre=rol.nombre,
            estado=rol.estado
        )
        
        return rol_actualizado
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rol_id}", status_code=status.HTTP_200_OK)
def delete_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar un rol.
    Solo se puede eliminar si no tiene usuarios asociados.
    Requiere permiso de borrar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar roles'
            )
        
        result = crud_roles.delete_rol(db, rol_id)
        
        return result
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rol_id}/usuarios", status_code=status.HTTP_200_OK)
def get_usuarios_by_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener la lista de usuarios con un rol específico.
    Requiere permiso de seleccionar en módulo Roles.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver roles'
            )
        
        usuarios = crud_roles.get_usuarios_by_rol(db, rol_id)
        
        return usuarios
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
