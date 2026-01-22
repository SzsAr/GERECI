"""
Router for firmas_digitales
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from app.schemas.firmas_digitales import FirmaDigitalCreate, FirmaDigitalOut
from app.schemas.users import UserOut
from app.crud import firmas_digitales as crud_firmas
from app.crud.permisos import verify_permissions
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 7  # Módulo 7: firmas_digitales


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_firma_digital(
    firma: FirmaDigitalCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Registrar una firma digital en un documento.
    Solo puede haber una firma por documento.
    Requiere permiso de insertar en módulo Firmas Digitales.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para registrar firmas digitales'
            )
        
        # Crear firma
        firma_id = crud_firmas.create_firma_digital(db, firma)
        
        return {
            "message": "Firma digital registrada correctamente",
            "firma_id": firma_id
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{firma_id}", response_model=FirmaDigitalOut, status_code=status.HTTP_200_OK)
def get_firma_digital(
    firma_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener firma digital por ID.
    Requiere permiso de seleccionar en módulo Firmas Digitales.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver firmas digitales'
            )
        
        firma = crud_firmas.get_firma_by_id(db, firma_id)
        
        if not firma:
            raise HTTPException(status_code=404, detail="Firma digital no encontrada")
        
        return firma
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documento/{documento_id}", response_model=FirmaDigitalOut, 
            status_code=status.HTTP_200_OK)
def get_firma_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener firma digital de un documento.
    Requiere permiso de seleccionar en módulo Firmas Digitales.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver firmas digitales'
            )
        
        firma = crud_firmas.get_firma_by_documento(db, documento_id)
        
        if not firma:
            raise HTTPException(status_code=404, detail="Este documento no tiene firma digital")
        
        return firma
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usuario/{usuario_id}", response_model=List[FirmaDigitalOut], 
            status_code=status.HTTP_200_OK)
def get_firmas_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las firmas digitales realizadas por un usuario.
    Requiere permiso de seleccionar en módulo Firmas Digitales.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver firmas digitales'
            )
        
        firmas = crud_firmas.get_firmas_by_usuario(db, usuario_id)
        
        return firmas
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{firma_id}", status_code=status.HTTP_200_OK)
def delete_firma_digital(
    firma_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar una firma digital.
    Requiere permiso de borrar en módulo Firmas Digitales.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar firmas digitales'
            )
        
        # Verificar que la firma exista
        firma = crud_firmas.get_firma_by_id(db, firma_id)
        if not firma:
            raise HTTPException(status_code=404, detail="Firma digital no encontrada")
        
        # Eliminar
        crud_firmas.delete_firma_digital(db, firma_id)
        
        return {"message": "Firma digital eliminada correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
