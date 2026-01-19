
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud.users import get_user_by_id, get_user_by_username
from core.security import verify_password, verify_token
from core.database import get_db
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

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
    # Acceder a estado como atributo (RowMapping)
    if hasattr(user_db, 'estado'):
        estado = user_db.estado
    else:
        estado = user_db.get('estado', True)
    
    if not estado:
        raise HTTPException(status_code=403, detail="Usuario inactivo. No autorizado")
    return user_db


def authenticate_user(username: str, password: str, db: Session):
    user = get_user_by_username(db, username)
    if not user:
        print(f"auth: usuario '{username}' no encontrado")
        return False
    if not verify_password(password, user.pass_hash):
        print(f"auth: contraseña inválida para '{username}'")
        return False
    print(f"auth: login OK para '{username}' (id={user.id_usuario})")
    return user