"""
Router for documentos
"""
from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import json
import os
import logging
from pathlib import Path

from core.database import get_db
from app.schemas.documentos import DocumentoCreate, DocumentoUpdate, DocumentoOut, DocumentoStateChange
from app.schemas.observaciones import ObservacionCreate
from app.schemas.users import UserOut
from app.crud import documentos as crud_documentos
from app.crud import observaciones as crud_observaciones
from app.crud.permisos import verify_permissions
from app.crud.firmas_digitales import registrar_firma_aprobacion, get_firmas_by_documento
from app.api.dependencies import get_current_user
from app.utils.document_generator import (
    generar_word_desde_plantilla,
    incrustar_firma,
    convertir_word_a_pdf,
    eliminar_archivo_documento,
    DOCUMENTOS_DIR
)
from app.crud.plantillas import get_plantilla_by_id
from app.utils.dynamic_data import actualizar_consecutivo_en_tabla_dinamica, actualizar_firmas_en_tabla_dinamica
from app.utils.dynamic_tables import obtener_nombre_tabla_plantilla

logger = logging.getLogger(__name__)

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
        
        # Log de entrada
        logger.info(f"Actualizando documento {documento_id}, valores_campos: {documento_update.valores_campos}")
        
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
        result = crud_documentos.update_documento(db, documento_id, documento_update)
        
        if not result:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el documento")
        
        return {"message": "Documento actualizado correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Error SQL al actualizar documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{documento_id}/estado", status_code=status.HTTP_200_OK)
def cambiar_estado_documento_endpoint(
    documento_id: int,
    cambio_estado: DocumentoStateChange,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Cambiar el estado de un documento.
    Si el nuevo estado es FINALIZADO, el trigger asigna automáticamente 
    el consecutivo y se genera el PDF final.
    
    Requiere permiso de actualizar en módulo Documentos.
    
    Estados válidos según flujo:
    - BORRADOR → EN_REVISION_JURIDICA (si requiere jurídica) o EN_REVISION_GERENCIAL
    - EN_REVISION_JURIDICA → APROBADO_JURIDICA o DEVUELTO_JURIDICA
    - DEVUELTO_JURIDICA → EN_REVISION_JURIDICA
    - APROBADO_JURIDICA → EN_REVISION_GERENCIAL
    - EN_REVISION_GERENCIAL → APROBADO_GERENCIA o DEVUELTO_GERENCIA
    - APROBADO_GERENCIA → FIRMADO
    - DEVUELTO_GERENCIA → EN_REVISION_JURIDICA (si requiere) o EN_REVISION_GERENCIAL
    - FIRMADO → FINALIZADO
    - PENDIENTE_FINALIZACION → FINALIZADO
    - FINALIZADO → (final, no más transiciones)
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
        
        # Validar observaciones si es devolución
        if cambio_estado.nuevo_estado in ['DEVUELTO_JURIDICA', 'DEVUELTO_GERENCIA']:
            descripcion = (cambio_estado.descripcion_cambio or '').strip()
            if not descripcion:
                raise HTTPException(
                    status_code=400,
                    detail='Debe ingresar observaciones para devolver el documento'
                )

        # Solo el creador puede finalizar el documento
        if cambio_estado.nuevo_estado == 'FINALIZADO':
            usuario_genera = documento.get('usuario_genera') if isinstance(documento, dict) else documento.usuario_genera
            if usuario_genera != user_token.id_usuario:
                raise HTTPException(
                    status_code=403,
                    detail='Solo el creador del documento puede finalizarlo'
                )

        # Cambiar estado (validaciones incluidas en la función)
        crud_documentos.cambiar_estado_documento(
            db, 
            documento_id, 
            cambio_estado.nuevo_estado
        )

        # Registrar observaciones si es devolución
        if cambio_estado.nuevo_estado in ['DEVUELTO_JURIDICA', 'DEVUELTO_GERENCIA']:
            tipo_obs = 'JURIDICA' if cambio_estado.nuevo_estado == 'DEVUELTO_JURIDICA' else 'GERENCIA'
            observacion = ObservacionCreate(
                id_documento=documento_id,
                id_usuario=user_token.id_usuario,
                tipo=tipo_obs,
                descripcion=cambio_estado.descripcion_cambio.strip()
            )
            crud_observaciones.create_observacion(db, observacion)
            
            # Eliminar archivos .docx cuando se devuelve
            try:
                eliminar_archivo_documento(documento_id)
                logger.info(f"Archivos .docx del documento {documento_id} eliminados al devolver")
            except Exception as e:
                logger.warning(f"No se pudieron eliminar archivos .docx del documento {documento_id} al devolver: {e}")

        
        # Registrar firma si es un estado de aprobación
        # Las firmas se registran ANTES de llegar a FIRMADO para que estén disponibles
        estados_con_firma = ['APROBADO_JURIDICA', 'APROBADO_GERENCIA']
        if cambio_estado.nuevo_estado in estados_con_firma:
            registrar_firma_aprobacion(db, documento_id, user_token.id_usuario)
            logger.info(f"Firma registrada para usuario {user_token.id_usuario} en estado {cambio_estado.nuevo_estado}")
        
        # Si es FIRMADO (APROBADO_GERENCIA → FIRMADO), regenerar Word con todas las firmas
        if cambio_estado.nuevo_estado == 'FIRMADO':
            # Asegurar que el usuario creador (quien elaboró) esté registrado como firma
            usuario_genera = documento.get('usuario_genera') if isinstance(documento, dict) else documento.usuario_genera
            if usuario_genera:
                registrar_firma_aprobacion(db, documento_id, usuario_genera)
                logger.info(f"Firma del creador (usuario {usuario_genera}) registrada al pasar a FIRMADO")
            
            # IMPORTANTE: Hacer commit para que las firmas estén disponibles al generar el context
            db.commit()
            
            # DEBUG: Verificar cuántas firmas hay registradas antes de generar el context
            from app.crud.firmas_digitales import get_firmas_by_documento
            firmas_debug = get_firmas_by_documento(db, documento_id)
            logger.info(f"DEBUG FIRMADO: Documento {documento_id} tiene {len(firmas_debug) if firmas_debug else 0} firmas registradas")
            if firmas_debug:
                for firma in firmas_debug:
                    logger.info(f"  - Usuario: {firma.get('nombre_usuario')}, Rol: {firma.get('id_rol')}, Cargo: {firma.get('cargo')}")
            
            try:
                # Obtener plantilla
                id_plantilla = documento.get('id_plantilla') if isinstance(documento, dict) else documento.id_plantilla
                plantilla = get_plantilla_by_id(db, id_plantilla)
                
                if plantilla:
                    nombre_archivo = plantilla.get('nombre_archivo')
                    ruta_almacenamiento = plantilla.get('ruta_almacenamiento')
                    
                    if nombre_archivo or ruta_almacenamiento:
                        # Construir ruta
                        if ruta_almacenamiento:
                            plantilla_path = Path(ruta_almacenamiento)
                        else:
                            plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / nombre_archivo
                        
                        if plantilla_path.exists():
                            # Generar context completo CON todas las firmas de aprobadores
                            context = crud_documentos.generar_context_con_firmas(db, documento_id)
                            logger.info(f"Context generado para documento {documento_id} en estado FIRMADO")
                            logger.info(f"DEBUG: Campos de firmas en context:")
                            logger.info(f"  - gerente_nombre: '{context.get('gerente_nombre')}'")
                            logger.info(f"  - gerente_cargo: '{context.get('gerente_cargo')}'")
                            logger.info(f"  - unidad_nombre: '{context.get('unidad_nombre')}'")
                            logger.info(f"  - unidad_cargo: '{context.get('unidad_cargo')}'")
                            logger.info(f"  - juridica_nombre: '{context.get('juridica_nombre')}'")
                            logger.info(f"  - juridica_cargo: '{context.get('juridica_cargo')}'")
                            
                            # Generar Word con firmas
                            ruta_word_firmado = generar_word_desde_plantilla(
                                str(plantilla_path),
                                documento_id,
                                context,
                                output_filename=f"{documento_id}_firmado.docx"
                            )

                            # Actualizar ruta del Word firmado
                            crud_documentos.update_documento(
                                db,
                                documento_id,
                                DocumentoUpdate(ruta_word_generado=ruta_word_firmado)
                            )
                            
                            # ⭐ ACTUALIZAR TABLA DINÁMICA CON FIRMAS (igual como funciona en FINALIZADO)
                            try:
                                nombre_tabla = obtener_nombre_tabla_plantilla(db, id_plantilla)
                                if nombre_tabla:
                                    # Actualizar firmas en tabla dinámica
                                    actualizar_firmas_en_tabla_dinamica(db, documento_id, nombre_tabla, context)
                                    logger.info(f"Firmas actualizadas en tabla dinámica para documento {documento_id} en estado FIRMADO")
                                else:
                                    logger.warning(f"No se encontró tabla dinámica para plantilla {id_plantilla}")
                            except Exception as e:
                                logger.error(f"Error al actualizar firmas en tabla dinámica en FIRMADO: {e}", exc_info=True)
                            
                            logger.info(f"Word generado con firmas para documento {documento_id}: {ruta_word_firmado}")
                            
                            return {
                                "message": "Documento firmado y Word generado con todas las firmas",
                                "nuevo_estado": "FIRMADO",
                                "ruta_word": ruta_word_firmado,
                                "info": "Puede visualizar el documento Word con las firmas antes de finalizar"
                            }
            except Exception as e:
                logger.error(f"Error al generar Word con firmas: {e}")
                # Continuar aunque falle la generación
                return {
                    "message": f"Documento marcado como FIRMADO pero hubo error al generar Word: {str(e)}",
                    "nuevo_estado": "FIRMADO",
                    "error": str(e)
                }
        
        # Si es FINALIZADO, asignar consecutivo y generar PDF final
        if cambio_estado.nuevo_estado == 'FINALIZADO':
            # Refrescar documento para obtener consecutivo asignado por trigger
            db.commit()  # Asegurar que el trigger se ejecutó
            documento_actualizado = crud_documentos.get_documento_by_id(db, documento_id)
            
            # Asegurar que el usuario creador (quien elaboró) esté registrado como firma
            usuario_genera = documento_actualizado.get('usuario_genera') if isinstance(documento_actualizado, dict) else documento_actualizado.usuario_genera
            if usuario_genera:
                registrar_firma_aprobacion(db, documento_id, usuario_genera)
            consecutivo = documento_actualizado.get('consecutivo') if isinstance(documento_actualizado, dict) else documento_actualizado.consecutivo
            
            if not consecutivo:
                raise HTTPException(
                    status_code=500,
                    detail="El trigger no asignó consecutivo correctamente"
                )
            
            # Actualizar consecutivo y firmas en la tabla dinámica del documento
            try:
                id_plantilla = documento_actualizado.get('id_plantilla') if isinstance(documento_actualizado, dict) else documento_actualizado.id_plantilla
                nombre_tabla = obtener_nombre_tabla_plantilla(db, id_plantilla)
                if nombre_tabla:
                    actualizar_consecutivo_en_tabla_dinamica(db, documento_id, nombre_tabla, consecutivo)
                    
                    # Generar context con firmas para actualizar en tabla dinámica
                    try:
                        context = crud_documentos.generar_context_con_firmas(db, documento_id)
                        actualizar_firmas_en_tabla_dinamica(db, documento_id, nombre_tabla, context)
                        logger.info(f"Firmas actualizadas en tabla dinámica para documento {documento_id}")
                    except Exception as e:
                        logger.warning(f"No se pudieron actualizar firmas en tabla dinámica: {e}")
            except Exception as e:
                logger.warning(f"No se pudo actualizar consecutivo/firmas en tabla dinámica: {e}")
            
            # Generar PDF final con consecutivo y fecha
            try:
                # Obtener plantilla
                id_plantilla = documento_actualizado.get('id_plantilla') if isinstance(documento_actualizado, dict) else documento_actualizado.id_plantilla
                plantilla = get_plantilla_by_id(db, id_plantilla)
                
                if plantilla:
                    nombre_archivo = plantilla.get('nombre_archivo')
                    ruta_almacenamiento = plantilla.get('ruta_almacenamiento')
                    
                    if nombre_archivo or ruta_almacenamiento:
                        # Construir ruta
                        if ruta_almacenamiento:
                            plantilla_path = Path(ruta_almacenamiento)
                        else:
                            plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / nombre_archivo
                        
                        if plantilla_path.exists():
                            # Obtener el Word firmado actual (ya tiene las firmas inyectadas)
                            ruta_word_firmado = documento_actualizado.get('ruta_word_generado') if isinstance(documento_actualizado, dict) else documento_actualizado.ruta_word_generado
                            
                            # SIEMPRE regenerar con context completo (firmas + consecutivo)
                            # para asegurar que el PDF final incluya todas las firmas
                            logger.info(f"Regenerando Word para documento {documento_id} con firmas y consecutivo")
                            context = crud_documentos.generar_context_con_firmas(db, documento_id)
                            context['consecutivo'] = consecutivo
                            
                            ruta_word_final = generar_word_desde_plantilla(
                                str(plantilla_path),
                                documento_id,
                                context,
                                output_filename=f"{documento_id}_final.docx"
                            )
                            
                            crud_documentos.update_documento(
                                db,
                                documento_id,
                                DocumentoUpdate(ruta_word_generado=ruta_word_final)
                            )
                            
                            ruta_word_firmado = ruta_word_final
                            
                            # Convertir a PDF con nombre personalizado
                            word_filename = ruta_word_firmado.replace('/static/documentos/', '')
                            word_full_path = DOCUMENTOS_DIR / word_filename
                            tipo_documento = documento_actualizado.get('tipo_nombre') if isinstance(documento_actualizado, dict) else documento_actualizado.tipo_nombre
                            ruta_pdf = convertir_word_a_pdf(
                                str(word_full_path),
                                documento_id,
                                tipo_documento=tipo_documento,
                                consecutivo=consecutivo
                            )
                            
                            if ruta_pdf:
                                crud_documentos.update_documento(
                                    db,
                                    documento_id,
                                    DocumentoUpdate(ruta_pdf_final=ruta_pdf)
                                )
                                
                                # Eliminar archivos .docx para liberar espacio
                                try:
                                    eliminar_archivo_documento(documento_id)
                                    logger.info(f"Archivos .docx del documento {documento_id} eliminados")
                                except Exception as e:
                                    logger.warning(f"No se pudieron eliminar archivos .docx del documento {documento_id}: {e}")
                                
                                return {
                                    "message": "Documento finalizado y PDF generado correctamente",
                                    "nuevo_estado": "FINALIZADO",
                                    "consecutivo": consecutivo,
                                    "ruta_word": ruta_word_firmado,
                                    "ruta_pdf": ruta_pdf
                                }

                            return {
                                "message": "Documento finalizado y Word generado. PDF pendiente",
                                "nuevo_estado": "FINALIZADO",
                                "consecutivo": consecutivo,
                                "ruta_word": ruta_word_firmado,
                                "ruta_pdf": None
                            }
            except Exception as e:
                # Si falla la generación de PDF, el documento igual queda FINALIZADO
                # pero sin PDF
                return {
                    "message": f"Documento finalizado pero error al generar PDF: {str(e)}",
                    "nuevo_estado": "FINALIZADO",
                    "consecutivo": consecutivo,
                    "error_pdf": str(e)
                }
            
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
    Eliminar documento en estado BORRADOR o DEVUELTO (DEVUELTO_JURIDICA, DEVUELTO_GERENCIA).
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
        
        # Verificar que el documento exista
        documento = crud_documentos.get_documento_by_id(db, documento_id)
        if not documento:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        estado = documento['estado'] if isinstance(documento, dict) else documento.estado
        
        # Permitir eliminar solo en estados BORRADOR o DEVUELTOS
        estados_eliminables = ['BORRADOR', 'DEVUELTO_JURIDICA', 'DEVUELTO_GERENCIA']
        if estado not in estados_eliminables:
            raise HTTPException(
                status_code=400,
                detail=f'Solo se pueden eliminar documentos en estado BORRADOR o DEVUELTO. Estado actual: {estado}'
            )
        
        # Obtener ruta del Word generado para eliminar después
        ruta_word = documento.get('ruta_word_generado') if isinstance(documento, dict) else documento.ruta_word_generado
        
        # Eliminar documento de la base de datos
        from sqlalchemy import text
        query = text("DELETE FROM documentos WHERE id = :documento_id")
        db.execute(query, {"documento_id": documento_id})
        db.commit()
        
        # Eliminar archivos .docx asociados
        try:
            eliminar_archivo_documento(documento_id, ruta_word)
            logger.info(f"Archivos .docx del documento {documento_id} eliminados")
        except Exception as e:
            logger.warning(f"No se pudieron eliminar archivos .docx del documento {documento_id}: {e}")
        
        return {"message": "Documento eliminado correctamente"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{documento_id}/generar-word", status_code=status.HTTP_200_OK)
def generar_word_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Generar documento Word desde la plantilla con los valores del documento.
    Se debe llamar antes de enviar a revisión.
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
        id_plantilla = documento.get('id_plantilla') if isinstance(documento, dict) else documento.id_plantilla
        plantilla = get_plantilla_by_id(db, id_plantilla)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Verificar que exista archivo de plantilla
        nombre_archivo = plantilla.get('nombre_archivo')
        ruta_almacenamiento = plantilla.get('ruta_almacenamiento')
        
        if not nombre_archivo and not ruta_almacenamiento:
            raise HTTPException(
                status_code=400, 
                detail="La plantilla no tiene archivo asociado. Por favor suba un archivo .docx a media/plantillas/"
            )
        
        # Construir ruta de la plantilla
        plantilla_path = None
        if ruta_almacenamiento:
            # Si ruta_almacenamiento es una ruta web (/static/plantillas/uuid.docx)
            # convertir a ruta física
            if ruta_almacenamiento.startswith('/static/plantillas/'):
                # Extraer nombre del archivo de la ruta web
                uuid_nombre = ruta_almacenamiento.replace('/static/plantillas/', '')
                plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / uuid_nombre
            else:
                # Si es una ruta física directa
                plantilla_path = Path(ruta_almacenamiento)
        else:
            # Asumir que está en media/plantillas/ con el nombre original
            plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / nombre_archivo
        
        if not plantilla_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo de plantilla no encontrado: {plantilla_path}"
            )
        
        estado_documento = documento.get('estado') if isinstance(documento, dict) else documento.estado

        # Si el documento ya está firmado/finalizado, usar contexto con firmas
        # para no sobrescribir el Word con placeholders de firma vacíos.
        if estado_documento in ['FIRMADO', 'PENDIENTE_FINALIZACION', 'FINALIZADO']:
            context = crud_documentos.generar_context_con_firmas(db, documento_id)
            output_filename = f"{documento_id}_firmado.docx" if estado_documento == 'FIRMADO' else f"{documento_id}_final.docx"
            logger.info(f"Generando Word para doc {documento_id} en estado {estado_documento} usando contexto con firmas")
        else:
            context = crud_documentos.generar_context_para_plantilla(db, documento_id, user_token.id_usuario)
            output_filename = None

        # Generar documento Word
        ruta_word = generar_word_desde_plantilla(
            str(plantilla_path),
            documento_id,
            context,
            output_filename=output_filename
        )
        
        # Actualizar documento con la ruta del Word generado
        update_data = DocumentoUpdate(ruta_word_generado=ruta_word)
        crud_documentos.update_documento(db, documento_id, update_data)
        
        return {
            "message": "Documento Word generado correctamente",
            "ruta_word": ruta_word,
            "documento_id": documento_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{documento_id}/generar-pdf", status_code=status.HTTP_200_OK)
def generar_pdf_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Generar PDF final del documento (después de FINALIZADO).
    El documento debe estar en estado FINALIZADO con consecutivo asignado.
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
        
        # Verificar que esté FINALIZADO
        estado = documento.get('estado') if isinstance(documento, dict) else documento.estado
        if estado != 'FINALIZADO':
            raise HTTPException(
                status_code=400,
                detail="El documento debe estar FINALIZADO para generar PDF"
            )
        
        # Verificar que tenga consecutivo asignado
        consecutivo = crud_documentos.obtener_consecutivo_asignado(db, documento_id)
        if not consecutivo:
            raise HTTPException(
                status_code=400,
                detail="El documento no tiene consecutivo asignado"
            )
        
        # Obtener plantilla
        id_plantilla = documento.get('id_plantilla') if isinstance(documento, dict) else documento.id_plantilla
        plantilla = get_plantilla_by_id(db, id_plantilla)
        if not plantilla:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Construir ruta de la plantilla
        nombre_archivo = plantilla.get('nombre_archivo')
        ruta_almacenamiento = plantilla.get('ruta_almacenamiento')
        
        if not nombre_archivo and not ruta_almacenamiento:
            raise HTTPException(
                status_code=400,
                detail="La plantilla no tiene archivo asociado"
            )
        
        plantilla_path = None
        if ruta_almacenamiento:
            # Si ruta_almacenamiento es una ruta web (/static/plantillas/uuid.docx)
            # convertir a ruta física
            if ruta_almacenamiento.startswith('/static/plantillas/'):
                # Extraer nombre del archivo de la ruta web
                uuid_nombre = ruta_almacenamiento.replace('/static/plantillas/', '')
                plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / uuid_nombre
            else:
                # Si es una ruta física directa
                plantilla_path = Path(ruta_almacenamiento)
        else:
            plantilla_path = Path(__file__).parent.parent.parent / "media" / "plantillas" / nombre_archivo
        
        if not plantilla_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo de plantilla no encontrado: {plantilla_path}"
            )
        
        # Generar contexto con firmas para evitar perder nombres/cargos en el Word final.
        context = crud_documentos.generar_context_con_firmas(db, documento_id)
        context['consecutivo'] = consecutivo
        
        # Generar documento Word FINAL
        ruta_word_final = generar_word_desde_plantilla(
            str(plantilla_path),
            documento_id,
            context,
            output_filename=f"{documento_id}_final.docx"
        )
        
        # Convertir Word a PDF con nombre personalizado
        word_filename = ruta_word_final.replace('/static/documentos/', '')
        word_full_path = DOCUMENTOS_DIR / word_filename
        
        tipo_documento = documento.get('tipo_nombre') if isinstance(documento, dict) else documento.tipo_nombre
        ruta_pdf = convertir_word_a_pdf(
            str(word_full_path),
            documento_id,
            tipo_documento=tipo_documento,
            consecutivo=consecutivo
        )
        
        if not ruta_pdf:
            raise HTTPException(
                status_code=500,
                detail="Error al convertir documento a PDF. Verifique que LibreOffice esté instalado."
            )
        
        # Actualizar documento con las rutas
        update_data = DocumentoUpdate(
            ruta_word_generado=ruta_word_final,
            ruta_pdf_final=ruta_pdf
        )
        crud_documentos.update_documento(db, documento_id, update_data)
        
        return {
            "message": "PDF final generado correctamente",
            "ruta_word": ruta_word_final,
            "ruta_pdf": ruta_pdf,
            "consecutivo": consecutivo,
            "documento_id": documento_id
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
        transiciones_validas = crud_documentos.obtener_transiciones_validas(db, documento_id, documento['estado'])
        if nuevo_estado not in transiciones_validas:
            raise HTTPException(
                status_code=400,
                detail=f'Transición no permitida. Estados válidos: {transiciones_validas}'
            )
        
        # Obtener documento Word generado
        if not documento.get('ruta_word_generado'):
            raise HTTPException(status_code=400, detail="Documento Word aún no ha sido generado")
        
        # Construir ruta completa del Word
        word_file = documento.get('ruta_word_generado', '').replace('/static/', '')
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
            consecutivo = crud_documentos.asignar_consecutivo(db, documento_id, documento['id_tipo'])
            
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
        
        estado_actual = documento.get('estado') if isinstance(documento, dict) else documento.estado
        transiciones = crud_documentos.obtener_transiciones_validas(db, documento_id, estado_actual)
        
        return {
            "estado_actual": estado_actual,
            "transiciones_validas": transiciones
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{documento_id}/firmas", status_code=status.HTTP_200_OK)
def obtener_firmas_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener todas las firmas digitales de un documento.
    Muestra el historial de aprobaciones con usuario, cargo y fecha.
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
        
        firmas = get_firmas_by_documento(db, documento_id)
        
        return {
            "documento_id": documento_id,
            "total_firmas": len(firmas),
            "firmas": firmas
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{documento_id}/datos", status_code=status.HTTP_200_OK)
def get_documento_datos(
    documento_id: int,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Obtener datos del documento en formato JSON.
    Retorna todos los campos necesarios para generar reportes.
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
        
        # Retornar documento completo como JSON
        return {
            "id_documento": documento.id_documento,
            "asunto": documento.asunto,
            "contenido": documento.contenido,
            "estado": documento.estado,
            "requiere_juridica": documento.requiere_juridica,
            "valores_campos": documento.valores_campos,
            "fecha_creacion": documento.fecha_creacion.isoformat() if documento.fecha_creacion else None,
            "fecha_finalizacion": documento.fecha_finalizacion.isoformat() if documento.fecha_finalizacion else None,
            "consecutivo": documento.consecutivo,
            "tipo_nombre": documento.tipo_nombre,
            "plantilla_nombre": documento.plantilla_nombre,
            "usuario_nombre": documento.usuario_nombre
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
