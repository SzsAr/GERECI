"""
Router for tipos_documentos management
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from app.crud import tipos_documentos as crud_tipos_documentos
from app.crud.permisos import verify_permissions
from app.schemas.tipos_documentos import TipoDocumentoCreate, TipoDocumentoUpdate, TipoDocumentoOut
from app.schemas.users import UserOut
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 11  # Módulo 11: tipos_documentos


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_tipo_documento(
    tipo_documento: TipoDocumentoCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Crear nuevo tipo de documento - requiere permiso de insertar"""
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear tipos de documentos'
            )
        
        id_nuevo = crud_tipos_documentos.create_tipo_documento(
            db, 
            tipo_documento.nombre, 
            tipo_documento.codigo, 
            tipo_documento.requiere_juridica
        )
        
        return {
            "message": "Tipo de documento creado correctamente",
            "id": id_nuevo
        }
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TipoDocumentoOut])
def get_all_tipos_documentos(
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Obtener todos los tipos de documentos - requiere permiso de seleccionar"""
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver tipos de documentos'
            )
        
        tipos = crud_tipos_documentos.get_all_tipos_documentos(db)
        return tipos
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tipo_id}", response_model=TipoDocumentoOut)
def get_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Obtener un tipo de documento por ID - requiere permiso de seleccionar"""
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver tipos de documentos'
            )
        
        tipo = crud_tipos_documentos.get_tipo_documento_by_id(db, tipo_id)
        if not tipo:
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
        
        return tipo
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tipo_id}", status_code=status.HTTP_200_OK)
def update_tipo_documento(
    tipo_id: int,
    tipo_documento: TipoDocumentoUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Actualizar tipo de documento - requiere permiso de actualizar"""
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar tipos de documentos'
            )
        
        # Verificar que el tipo de documento existe
        tipo_existente = crud_tipos_documentos.get_tipo_documento_by_id(db, tipo_id)
        if not tipo_existente:
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
        
        success = crud_tipos_documentos.update_tipo_documento(
            db,
            tipo_id,
            tipo_documento.nombre,
            tipo_documento.codigo,
            tipo_documento.requiere_juridica
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el tipo de documento")
        
        return {"message": "Tipo de documento actualizado correctamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tipo_id}", status_code=status.HTTP_200_OK)
def delete_tipo_documento(
    tipo_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Eliminar tipo de documento - requiere permiso de borrar"""
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar tipos de documentos'
            )
        
        # Verificar que el tipo de documento existe
        tipo_existente = crud_tipos_documentos.get_tipo_documento_by_id(db, tipo_id)
        if not tipo_existente:
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
        
        success = crud_tipos_documentos.delete_tipo_documento(db, tipo_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo eliminar el tipo de documento")
        
        return {"message": "Tipo de documento eliminado correctamente"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
