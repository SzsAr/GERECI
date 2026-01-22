from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Annotated

from app.schemas.cargos import CargoCreate, CargoUpdate, CargoOut
from app.schemas.users import UserOut
from app.crud import cargos as crud_cargos
from app.api.dependencies import get_db, get_current_user
from app.crud.permisos import verify_permissions


router = APIRouter()

# Cargos no tiene módulo propio en la DB, usar módulo usuarios (id=4) para permisos
modulo = 4


@router.post("/", response_model=CargoOut, status_code=status.HTTP_201_CREATED)
def create_cargo(
    cargo: CargoCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear un nuevo cargo.
    Requiere permiso de insertar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear cargos'
            )
        
        nuevo_cargo = crud_cargos.create_cargo(
            db, 
            nombre=cargo.nombre,
            descripcion=cargo.descripcion,
            estado=cargo.estado
        )
        
        return nuevo_cargo
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[CargoOut], status_code=status.HTTP_200_OK)
def get_cargos(
    solo_activos: bool = False,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todos los cargos.
    Si solo_activos=True, solo devuelve cargos con estado=1.
    Requiere permiso de seleccionar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver cargos'
            )
        
        cargos = crud_cargos.get_all_cargos(db, solo_activos)
        
        return cargos
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cargo_id}", response_model=CargoOut, status_code=status.HTTP_200_OK)
def get_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener un cargo por ID.
    Requiere permiso de seleccionar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver cargos'
            )
        
        cargo = crud_cargos.get_cargo_by_id(db, cargo_id)
        
        return cargo
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{cargo_id}", response_model=CargoOut, status_code=status.HTTP_200_OK)
def update_cargo(
    cargo_id: int,
    cargo: CargoUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Actualizar un cargo.
    Requiere permiso de actualizar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar cargos'
            )
        
        cargo_actualizado = crud_cargos.update_cargo(
            db, 
            cargo_id, 
            nombre=cargo.nombre,
            descripcion=cargo.descripcion,
            estado=cargo.estado
        )
        
        return cargo_actualizado
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cargo_id}", status_code=status.HTTP_200_OK)
def delete_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar un cargo.
    Solo se puede eliminar si no tiene usuarios asociados.
    Requiere permiso de borrar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar cargos'
            )
        
        result = crud_cargos.delete_cargo(db, cargo_id)
        
        return result
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cargo_id}/usuarios", status_code=status.HTTP_200_OK)
def get_usuarios_by_cargo(
    cargo_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener la lista de usuarios con un cargo específico.
    Requiere permiso de seleccionar en módulo Usuarios.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver cargos'
            )
        
        usuarios = crud_cargos.get_usuarios_by_cargo(db, cargo_id)
        
        return usuarios
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
