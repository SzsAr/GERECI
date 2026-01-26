"""
Router for documentos
"""
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
import os
from pathlib import Path

from core.database import get_db
from app.schemas.documentos import DocumentoCreate, DocumentoUpdate, DocumentoOut, DocumentoStateChange
from app.schemas.users import UserOut
from app.crud import documentos as crud_documentos
from app.crud.permisos import verify_permissions
from app.api.dependencies import get_current_user
from app.utils.document_generator import (
    generar_word_desde_plantilla,
    incrustar_firma,
    convertir_word_a_pdf,
    DOCUMENTOS_DIR
)
from app.crud.plantillas import get_plantilla_by_id

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
        
        estado = documento['estado'] if isinstance(documento, dict) else documento.estado
        if estado != 'BORRADOR':
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


@router.post("/{documento_id}/generar", status_code=status.HTTP_200_OK)
def generar_documento_word(
    documento_id: int,
    valores_campos: dict = None,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Generar documento Word desde la plantilla asociada.
    Requiere permiso de actualizar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para generar documentos'
            )
        
        # Obtener documento
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Obtener plantilla
        plantilla = get_plantilla_by_id(db, documento['id_plantilla'] if isinstance(documento, dict) else documento.id_plantilla)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Obtener ruta completa de la plantilla
        plantilla_ruta = plantilla['ruta_almacenamiento'] if isinstance(plantilla, dict) else plantilla.ruta_almacenamiento
        if plantilla_ruta.startswith('/static/'):
            plantilla_ruta = plantilla_ruta.replace('/static/', '')
        
        plantilla_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', plantilla_ruta)
        plantilla_path = os.path.normpath(plantilla_path)
        
        if not os.path.exists(plantilla_path):
            raise HTTPException(status_code=404, detail=f"Plantilla no encontrada en {plantilla_path}")
        
        # Usar valores_campos pasados como parámetro o vacío
        campos_para_plantilla = valores_campos or {}
        
        # Generar documento Word
        ruta_word = generar_word_desde_plantilla(plantilla_path, documento_id, campos_para_plantilla)
        
        # Actualizar documento con ruta del Word generado
        from app.crud import documentos as crud_doc
        update_data = DocumentoUpdate(ruta_word_generado=ruta_word)
        crud_doc.update_documento(db, documento_id, update_data)
        
        return {
            "message": "Documento Word generado correctamente",
            "ruta_word": ruta_word
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{documento_id}/firmar", status_code=status.HTTP_200_OK)
def firmar_documento(
    documento_id: int,
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Incrustar firma del usuario actual y cambiar estado del documento.
    Incluye imagen de firma, nombre y cargo del usuario.
    Requiere permiso de actualizar en módulo Documentos.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'actualizar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado para firmar documentos'
            )
        
        # Obtener documento
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Validar transición de estado
        transiciones_validas = crud_documentos.obtener_transiciones_validas(db, documento_id, documento.estado)
        if nuevo_estado not in transiciones_validas:
            raise HTTPException(
                status_code=400,
                detail=f'Transición no permitida. Estados válidos: {transiciones_validas}'
            )
        
        # Obtener documento Word generado
        if not documento.ruta_word_generado:
            raise HTTPException(status_code=400, detail="Documento Word aún no ha sido generado")
        
        # Construir ruta completa del Word
        word_file = documento.ruta_word_generado.replace('/static/', '')
        word_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', word_file)
        word_path = os.path.normpath(word_path)
        
        if not os.path.exists(word_path):
            raise HTTPException(status_code=404, detail="Documento Word no encontrado")
        
        # Obtener usuario que firma
        from app.crud.users import get_user_by_id
        usuario_firma = get_user_by_id(db, user_token.id_usuario)
        if not usuario_firma:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        usuario_nombre = usuario_firma.nombre if hasattr(usuario_firma, 'nombre') else usuario_firma.get('nombre', 'Desconocido')
        usuario_cargo = usuario_firma.cargo_nombre if hasattr(usuario_firma, 'cargo_nombre') else usuario_firma.get('cargo_nombre', '')
        
        # Obtener ruta de firma (si existe)
        firma_path = None
        firma_ruta = f"/static/firmas/firma_usuario_{user_token.id_usuario}.png"
        firma_file = f"firmas/firma_usuario_{user_token.id_usuario}.png"
        firma_path_temp = os.path.join(os.path.dirname(__file__), '..', '..', 'media', firma_file)
        firma_path_temp = os.path.normpath(firma_path_temp)
        if os.path.exists(firma_path_temp):
            firma_path = firma_path_temp
        
        # Incrustar firma en el documento
        ruta_word_firmado = incrustar_firma(
            word_path,
            documento_id,
            usuario_nombre,
            usuario_cargo,
            firma_path
        )
        
        # Cambiar estado
        crud_documentos.cambiar_estado_documento(db, documento_id, nuevo_estado)
        
        # Si es FINALIZADO, generar PDF y asignar consecutivo
        if nuevo_estado == 'FINALIZADO':
            # Generar PDF desde Word firmado
            word_firmado = ruta_word_firmado.replace('/static/', '')
            word_firmado_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', word_firmado)
            word_firmado_path = os.path.normpath(word_firmado_path)
            
            ruta_pdf = convertir_word_a_pdf(word_firmado_path, documento_id)
            if ruta_pdf:
                update_data = DocumentoUpdate(ruta_pdf_final=ruta_pdf)
                crud_documentos.update_documento(db, documento_id, update_data)
            
            # Asignar consecutivo
            consecutivo = crud_documentos.asignar_consecutivo(db, documento_id, documento.id_tipo)
            
            return {
                "message": "Documento finalizado correctamente",
                "nuevo_estado": nuevo_estado,
                "ruta_word": ruta_word_firmado,
                "ruta_pdf": ruta_pdf,
                "consecutivo": consecutivo
            }
        
        # Actualizar ruta del Word firmado
        update_data = DocumentoUpdate(ruta_word_generado=ruta_word_firmado)
        crud_documentos.update_documento(db, documento_id, update_data)
        
        return {
            "message": "Firma incrustrada y estado actualizado",
            "nuevo_estado": nuevo_estado,
            "ruta_word": ruta_word_firmado
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{documento_id}/transiciones", status_code=status.HTTP_200_OK)
def obtener_transiciones_validas(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener estados válidos a los que puede transitar el documento.
    """
    try:
        id_rol = user_token.id_rol
        
        # Verificar permisos
        if not verify_permissions(db, id_rol, modulo, 'seleccionar'):
            raise HTTPException(
                status_code=403,
                detail='Usuario no autorizado'
            )
        
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        transiciones = crud_documentos.obtener_transiciones_validas(db, documento_id, documento.estado)
        
        return {
            "estado_actual": documento.estado,
            "transiciones_validas": transiciones
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
