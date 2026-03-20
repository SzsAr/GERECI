
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import (
    AUTH_FAIL_INACTIVE_USER,
    authenticate_user,
)
from app.schemas.auth import ResponseLoggin, UserAuthOut
from core.security import create_access_token
from core.database import get_db
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()

@router.post("/token", response_model=ResponseLoggin)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user, reason = authenticate_user(
        form_data.username,
        form_data.password,
        db,
        include_reason=True,
    )
    if not user:
        if reason == AUTH_FAIL_INACTIVE_USER:
            raise HTTPException(
                status_code=403,
                detail="Usuario desactivado. Contacte al administrador",
            )
        raise HTTPException(
            status_code=401,
            detail="Datos Incorrectos en username o password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener cargo_nombre (ya viene del CRUD gracias a los JOINs)
    cargo_nombre = user.get('cargo_nombre') if isinstance(user, dict) else getattr(user, 'cargo_nombre', None)
    area_display = cargo_nombre or "Sin asignar"
    
    # Mapear a un esquema ligero para auth
    user_out = UserAuthOut(
        id_usuario=user.get('id_usuario') if isinstance(user, dict) else user.id_usuario,
        nombre=user.get('nombre') if isinstance(user, dict) else user.nombre,
        username=user.get('username') if isinstance(user, dict) else user.username,
        id_rol=user.get('id_rol') if isinstance(user, dict) else user.id_rol,
        rol_nombre=area_display,
        estado=user.get('estado') if isinstance(user, dict) else user.estado,
    )
    
    access_token = create_access_token(
        data={"sub": str(user.get('id_usuario') if isinstance(user, dict) else user.id_usuario), "rol": user.get('id_rol') if isinstance(user, dict) else user.id_rol}
    )

    return ResponseLoggin(
        user=user_out,
        access_token=access_token
    )