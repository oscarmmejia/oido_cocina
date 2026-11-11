from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser, get_current_user
from app.models.security_model import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone_number: str

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existe = db.query(User).filter(User.email == data.email).first()
    if existe:
        raise AppError("BAD_REQUEST", "El usuario ya existe.", 400)
        
    nuevo_usuario = User(
        name=data.name,
        email=data.email,
        password_hash=data.password, 
        phone_number=data.phone_number,
        token_version=0,
        is_active=True,
        restaurant_id=1,
        role_id=2
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return {"message": "Usuario registrado correctamente", "user_id": nuevo_usuario.id}

@router.post("/logout")
def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if db_user:
        db_user.token_version += 1
        db.commit()
    
    return {"detail": "Sesión cerrada correctamente. Token revocado."}