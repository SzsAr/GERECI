"""
Router for observaciones
"""
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from app.schemas.observaciones import ObservacionCreate, ObservacionUpdate, ObservacionOut
from app.schemas.users import UserOut
from app.crud import observaciones as crud_observaciones
from app.crud.permisos import verify_permissions
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 8  # Módulo 8: observaciones


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_observacion(
    observacion: ObservacionCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear nueva observación.
    Requiere permiso de insertar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear observaciones'
            )
        
        # Validar tipo de observación
        if observacion.tipo not in ['JURIDICA', 'GERENCIA']:
            raise HTTPException(
                status_code=400,
                detail='Tipo de observación inválido. Debe ser JURIDICA o GERENCIA'
            )
        
        # Crear observación
        observacion_id = crud_observaciones.create_observacion(db, observacion)
        
        return {
            "message": "Observación creada correctamente",
            "observacion_id": observacion_id
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{observacion_id}", response_model=ObservacionOut, status_code=status.HTTP_200_OK)
def get_observacion(
    observacion_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener observación por ID.
    Requiere permiso de seleccionar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver observaciones'
            )
        
        observacion = crud_observaciones.get_observacion_by_id(db, observacion_id)
        
        if not observacion:
            raise HTTPException(status_code=404, detail="Observación no encontrada")
        
        return observacion
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documento/{documento_id}", response_model=List[ObservacionOut], 
            status_code=status.HTTP_200_OK)
def get_observaciones_documento(
    documento_id: int,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las observaciones de un documento.
    Opcionalmente filtrar por tipo: JURIDICA o GERENCIA.
    Requiere permiso de seleccionar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver observaciones'
            )
        
        # Validar tipo si viene
        if tipo and tipo not in ['JURIDICA', 'GERENCIA']:
            raise HTTPException(
                status_code=400,
                detail='Tipo inválido. Debe ser JURIDICA o GERENCIA'
            )
        
        observaciones = crud_observaciones.get_observaciones_by_documento(
            db, 
            documento_id, 
            tipo
        )
        
        return observaciones
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usuario/{usuario_id}", response_model=List[ObservacionOut], 
            status_code=status.HTTP_200_OK)
def get_observaciones_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las observaciones realizadas por un usuario.
    Requiere permiso de seleccionar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver observaciones'
            )
        
        observaciones = crud_observaciones.get_observaciones_by_usuario(db, usuario_id)
        
        return observaciones
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{observacion_id}", status_code=status.HTTP_200_OK)
def update_observacion(
    observacion_id: int,
    observacion_update: ObservacionUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Actualizar una observación (solo descripción).
    Requiere permiso de actualizar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar observaciones'
            )
        
        # Verificar que la observación exista
        observacion = crud_observaciones.get_observacion_by_id(db, observacion_id)
        if not observacion:
            raise HTTPException(status_code=404, detail="Observación no encontrada")
        
        # Actualizar
        crud_observaciones.update_observacion(db, observacion_id, observacion_update)
        
        return {"message": "Observación actualizada correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{observacion_id}", status_code=status.HTTP_200_OK)
def delete_observacion(
    observacion_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar una observación.
    Requiere permiso de borrar en módulo Observaciones.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar observaciones'
            )
        
        # Verificar que la observación exista
        observacion = crud_observaciones.get_observacion_by_id(db, observacion_id)
        if not observacion:
            raise HTTPException(status_code=404, detail="Observación no encontrada")
        
        # Eliminar
        crud_observaciones.delete_observacion(db, observacion_id)
        
        return {"message": "Observación eliminada correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
