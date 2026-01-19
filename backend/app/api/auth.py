
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import authenticate_user
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
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Datos Incorrectos en username o password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mapear a un esquema ligero para auth
    user_out = UserAuthOut(
        id_usuario=user.id_usuario,
        nombre=user.nombre,
        username=user.username,
        id_rol=user.id_rol,
        estado=user.estado,
    )
    
    access_token = create_access_token(
        data={"sub": str(user.id_usuario), "rol": user.id_rol}
    )

    return ResponseLoggin(
        user=user_out,
        access_token=access_token
    )