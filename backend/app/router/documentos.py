"""
Router for documentos
"""
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_db
from app.schemas.documentos import DocumentoCreate, DocumentoUpdate, DocumentoOut, DocumentoStateChange
from app.schemas.users import UserOut
from app.crud import documentos as crud_documentos
from app.crud.permisos import verify_permissions
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 6  # Módulo 6: documentos (según tabla modulos)


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_documento(
    documento: DocumentoCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Crear nuevo documento en estado BORRADOR.
    Requiere permiso de insertar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'insertar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para crear documentos'
            )
        
        # Crear documento con el usuario autenticado como generador
        documento_id = crud_documentos.create_documento(db, documento, user_token.id_usuario)
        
        return {
            "message": "Documento creado correctamente",
            "documento_id": documento_id,
            "estado": "BORRADOR"
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{documento_id}", response_model=DocumentoOut, status_code=status.HTTP_200_OK)
def get_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener documento por ID.
    Requiere permiso de seleccionar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para ver documentos'
            )
        
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        return documento
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DocumentoOut], status_code=status.HTTP_200_OK)
def get_all_documentos(
    estado: Optional[str] = None,
    usuario_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todos los documentos con filtros opcionales.
    Requiere permiso de seleccionar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para listar documentos'
            )
        
        documentos = crud_documentos.get_all_documentos(
            db, 
            filtro_estado=estado,
            filtro_usuario=usuario_id
        )
        
        return documentos
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{documento_id}", status_code=status.HTTP_200_OK)
def update_documento(
    documento_id: int,
    documento_update: DocumentoUpdate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Actualizar campos del documento (no el estado).
    Requiere permiso de actualizar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para actualizar documentos'
            )
        
        # Verificar que el documento exista
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Actualizar
        crud_documentos.update_documento(db, documento_id, documento_update)
        
        return {"message": "Documento actualizado correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{documento_id}/estado", status_code=status.HTTP_200_OK)
def cambiar_estado_documento(
    documento_id: int,
    cambio_estado: DocumentoStateChange,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Cambiar el estado de un documento.
    Requiere permiso de actualizar en módulo Documentos.
    
    Estados válidos:
    - BORRADOR
    - EN_REVISION_JURIDICA
    - EN_REVISION_GERENCIAL
    - APROBADO_JURIDICA
    - APROBADO_GERENCIA
    - FIRMADO
    - DEVUELTO_JURIDICA
    - DEVUELTO_GERENCIA
    - PENDIENTE_FINALIZACION
    - FINALIZADO
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para cambiar estado de documentos'
            )
        
        # Verificar que el documento exista
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Cambiar estado
        crud_documentos.cambiar_estado_documento(
            db, 
            documento_id, 
            cambio_estado.nuevo_estado
        )
        
        # Si es FINALIZADO, asignar consecutivo
        if cambio_estado.nuevo_estado == 'FINALIZADO':
            consecutivo = crud_documentos.asignar_consecutivo(
                db, 
                documento_id, 
                documento.id_tipo
            )
            return {
                "message": "Documento finalizado correctamente",
                "nuevo_estado": "FINALIZADO",
                "consecutivo": consecutivo
            }
        
        return {
            "message": "Estado del documento actualizado correctamente",
            "nuevo_estado": cambio_estado.nuevo_estado
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{documento_id}", status_code=status.HTTP_200_OK)
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Eliminar documento (solo BORRADORES).
    Requiere permiso de borrar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'borrar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para eliminar documentos'
            )
        
        # Verificar que el documento exista y esté en BORRADOR
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        if documento.estado != 'BORRADOR':
            raise HTTPException(
                status_code=400,
                detail='Solo se pueden eliminar documentos en estado BORRADOR'
            )
        
        # Eliminar documento
        from sqlalchemy import text
        query = text("DELETE FROM documentos WHERE id = :documento_id")
        db.execute(query, {"documento_id": documento_id})
        db.commit()
        
        return {"message": "Documento eliminado correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
