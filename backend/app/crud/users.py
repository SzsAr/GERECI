
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from app.schemas.users import UserCreate, UserUpdate
from core.security import get_hashed_password

logger = logging.getLogger(__name__)

def create_user(db: Session, user: UserCreate) -> Optional[bool]:
    try:
        query = text("""
            INSERT INTO usuarios (
                nombre, documento, username, id_rol,
                pass_hash, firma, estado
            ) VALUES (
                :nombre, :documento, :username, :id_rol,
                :pass_hash, :firma, :estado
            )
        """)
        params = user.model_dump()
        if params.get("pass_hash"):
            params["pass_hash"] = get_hashed_password(params["pass_hash"]) 
        db.execute(query, params)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error al crear usuario: {e}")
        raise Exception("Error de base de datos al crear el usuario")

def get_user_by_username(db: Session, username: str):
    try:
        query = text("""
            SELECT 
                id AS id_usuario,
                nombre,
                documento,
                username,
                id_rol,
                pass_hash,
                firma,
                estado
            FROM usuarios 
            WHERE username = :username
        """)
        result = db.execute(query, {"username": username}).mappings().first()
        return result
    except Exception as e:
        logger.error(f"Error al obtener usuario por username: {e}")
        raise Exception("Error de base de datos al obtener el usuario")

def get_user_by_id(db: Session, user_id: int):
    try:
        query = text("""
            SELECT 
                id AS id_usuario,
                nombre,
                documento,
                username,
                id_rol,
                pass_hash,
                firma,
                estado
            FROM usuarios 
            WHERE id = :user_id
        """)
        result = db.execute(query, {"user_id": user_id}).mappings().first()
        return result
    except Exception as e:
        logger.error(f"Error al obtener usuario por id: {e}")
        raise Exception("Error de base de datos al obtener el usuario")

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> bool:
    try:
        fields = user_update.model_dump(exclude_unset=True)
        if not fields:
            return False
        # Si viene nueva contraseña, hashearla antes de actualizar
        if "pass_hash" in fields and fields["pass_hash"] is not None:
            fields["pass_hash"] = get_hashed_password(fields["pass_hash"]) 
        set_clause = ", ".join([f"{key} = :{key}" for key in fields])
        fields["user_id"] = user_id

        query = text(f"UPDATE usuarios SET {set_clause} WHERE id = :user_id")
        db.execute(query, fields)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar usuario: {e}")
        raise Exception("Error de base de datos al actualizar el usuario")