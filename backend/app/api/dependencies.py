
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud.users import get_user_by_id, get_user_by_username
from core.security import verify_password, verify_token
from core.database import get_db
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

AUTH_FAIL_INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
AUTH_FAIL_INACTIVE_USER = "INACTIVE_USER"


def _get_user_field(user, field: str, default=None):
    if user is None:
        return default
    if isinstance(user, dict):
        return user.get(field, default)
    if hasattr(user, field):
        return getattr(user, field)
    try:
        return user.get(field, default)
    except Exception:
        return default

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token Invalido")
    user_db = get_user_by_id(db, user_id)
    if user_db is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    estado = _get_user_field(user_db, "estado", True)
    if not bool(estado):
        raise HTTPException(status_code=403, detail="Usuario inactivo. No autorizado")
    return user_db


def authenticate_user(
    username: str,
    password: str,
    db: Session,
    include_reason: bool = False,
):
    def _result(user, reason: Optional[str] = None):
        if include_reason:
            return user, reason
        return user if user else False

    user = get_user_by_username(db, username)
    if not user:
        print(f"auth: usuario '{username}' no encontrado")
        return _result(False, AUTH_FAIL_INVALID_CREDENTIALS)

    # No permitir inicio de sesión para usuarios inactivos.
    estado = _get_user_field(user, "estado", True)
    if not bool(estado):
        print(f"auth: usuario inactivo '{username}'")
        return _result(False, AUTH_FAIL_INACTIVE_USER)

    pass_hash = _get_user_field(user, "pass_hash")
    if not pass_hash or not verify_password(password, pass_hash):
        print(f"auth: contraseña inválida para '{username}'")
        return _result(False, AUTH_FAIL_INVALID_CREDENTIALS)

    user_id = _get_user_field(user, "id_usuario", "?")
    print(f"auth: login OK para '{username}' (id={user_id})")
    return _result(user, None)