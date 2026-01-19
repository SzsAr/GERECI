
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated
from pathlib import Path
import uuid
from core.database import get_db
from app.schemas.users import UserCreate, UserUpdate, UserOut
from app.crud import users as crud_users
from app.api.dependencies import get_current_user

# Directorio para guardar firmas
FIRMAS_DIR = Path(__file__).parent.parent.parent / "media" / "firmas"
FIRMAS_DIR.mkdir(parents=True, exist_ok=True)

# Tipos MIME permitidos para firmas
ALLOWED_MIMETYPES = {"image/png", "image/webp", "image/jpeg"}
MAX_FILE_SIZE = 100 * 1024  # 100 KB

router = APIRouter()

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    print("id de rol ", user_token.id_rol, " su tipo ", type(user_token.id_rol))

    # Solo superadmin (rol 1) puede crear usuarios
    if user_token.id_rol != 1:
        raise HTTPException(
            status_code=403,
            detail="Permiso denegado: solo el rol SuperAdmin (1) puede crear usuarios"
        )
    
    try:
        crud_users.create_user(db, user)
        return {"message": "Usuario creado correctamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", status_code=status.HTTP_200_OK)
def get_user(
    username: str, 
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Obtener usuario por username (requiere autenticación)"""
    try:
        user = crud_users.get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(
    user_id: int, 
    user: UserUpdate, 
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """Actualizar usuario (requiere autenticación)"""
    try:
        success = crud_users.update_user(db, user_id, user)
        if not success:
            raise HTTPException(status_code=400, detail="No se pudo actualizar el usuario")
        return {"message": "Usuario actualizado correctamente"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/firma", status_code=status.HTTP_200_OK)
def upload_firma(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_token: Annotated[UserOut, Depends(get_current_user)] = None
):
    """
    Subir firma de usuario. 
    Solo superadmin (rol 1) puede subir firmas.
    Formatos permitidos: PNG, WebP, JPEG. Máximo 100 KB.
    """
    # Solo superadmin puede subir firmas
    if user_token.id_rol != 1:
        raise HTTPException(
            status_code=403,
            detail="Permiso denegado: solo superadmin puede subir firmas"
        )
    
    # Validar MIME type
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Formatos: {', '.join(ALLOWED_MIMETYPES)}"
        )
    
    try:
        # Leer contenido del archivo
        contents = file.file.read()
        
        # Validar tamaño
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Archivo demasiado grande. Máximo {MAX_FILE_SIZE // 1024} KB"
            )
        
        # Obtener usuario actual
        user_db = crud_users.get_user_by_id(db, user_id)
        if not user_db:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Limpiar firma anterior si existe
        if user_db.firma and user_db.firma.startswith("/static/firmas/"):
            old_filename = user_db.firma.split("/")[-1]
            old_filepath = FIRMAS_DIR / old_filename
            if old_filepath.exists():
                old_filepath.unlink()
        
        # Generar nombre único para el archivo
        file_ext = file.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{file_ext}"
        filepath = FIRMAS_DIR / filename
        
        # Guardar archivo
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Construir URL pública
        firma_url = f"/static/firmas/{filename}"
        
        # Actualizar URL en BD
        from app.schemas.users import UserUpdate as UserUpdateSchema
        user_update = UserUpdateSchema(firma=firma_url)
        crud_users.update_user(db, user_id, user_update)
        
        return {
            "message": "Firma subida correctamente",
            "firma_url": firma_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar firma: {str(e)}")