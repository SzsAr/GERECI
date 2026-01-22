"""
Router for tareas_pendientes
"""
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from app.schemas.tareas_pendientes import TareaPendienteCreate, TareaPendienteOut
from app.schemas.users import UserOut
from app.crud import tareas_pendientes as crud_tareas
from app.crud.permisos import verify_permissions
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 10  # Módulo 10: tareas_pendientes


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_tarea(
    tarea: TareaPendienteCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear nueva tarea pendiente.
    Requiere permiso de insertar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear tareas pendientes'
            )
        
        # Crear tarea
        tarea_id = crud_tareas.create_tarea(db, tarea)
        
        return {
            "message": "Tarea pendiente creada correctamente",
            "tarea_id": tarea_id
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tarea_id}", response_model=TareaPendienteOut, status_code=status.HTTP_200_OK)
def get_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener tarea pendiente por ID.
    Requiere permiso de seleccionar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver tareas pendientes'
            )
        
        tarea = crud_tareas.get_tarea_by_id(db, tarea_id)
        
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        return tarea
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mis-tareas", response_model=List[TareaPendienteOut], 
            status_code=status.HTTP_200_OK)
def get_mis_tareas(
    solo_pendientes: bool = True,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener las tareas del área del usuario autenticado.
    El área se determina por el rol del usuario (id_rol = id_area).
    Por defecto solo devuelve las pendientes (completada=False).
    Este endpoint NO requiere verificación de permisos adicional.
    """
    try:
        # El area_id es igual al id_rol del usuario
        area_id = user_token.id_rol
        
        # Obtener tareas del área
        tareas = crud_tareas.get_tareas_by_area(
            db, 
            area_id, 
            solo_pendientes
        )
        
        return tareas
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/area/{area_id}", response_model=List[TareaPendienteOut], 
            status_code=status.HTTP_200_OK)
def get_tareas_area(
    area_id: int,
    solo_pendientes: bool = False,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener tareas de un área específica (para administradores).
    Si solo_pendientes=True, solo devuelve las no completadas.
    Requiere permiso de seleccionar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver tareas pendientes'
            )
        
        tareas = crud_tareas.get_tareas_by_area(db, area_id, solo_pendientes)
        
        return tareas
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documento/{documento_id}", response_model=List[TareaPendienteOut], 
            status_code=status.HTTP_200_OK)
def get_tareas_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las tareas asociadas a un documento.
    Requiere permiso de seleccionar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver tareas pendientes'
            )
        
        tareas = crud_tareas.get_tareas_by_documento(db, documento_id)
        
        return tareas
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{tarea_id}/completar", status_code=status.HTTP_200_OK)
def completar_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Marcar una tarea como completada.
    Requiere permiso de actualizar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para completar tareas pendientes'
            )
        
        # Verificar que la tarea exista
        tarea = crud_tareas.get_tarea_by_id(db, tarea_id)
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Completar tarea
        crud_tareas.completar_tarea(db, tarea_id)
        
        return {"message": "Tarea completada correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tarea_id}", status_code=status.HTTP_200_OK)
def delete_tarea(
    tarea_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar una tarea pendiente.
    Requiere permiso de borrar en módulo Tareas Pendientes.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar tareas pendientes'
            )
        
        # Verificar que la tarea exista
        tarea = crud_tareas.get_tarea_by_id(db, tarea_id)
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Eliminar tarea
        crud_tareas.delete_tarea(db, tarea_id)
        
        return {"message": "Tarea eliminada correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
