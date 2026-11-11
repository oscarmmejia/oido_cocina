from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser, get_current_user
from app.models.security_model import User

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- ESQUEMAS PARA RECIBIR DATOS ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str


# --- 1. REGISTER ---
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existe = db.query(User).filter(User.email == data.email).first()
    if existe:
        raise AppError("BAD_REQUEST", "El usuario ya existe.", 400)
        
    # (Nota: En un proyecto real aquí hashearías la contraseña)
    nuevo_usuario = User(
        email=data.email,
        password=data.password, 
        token_version=0,
        is_active=True,
        restaurant_id=1  # Ajusta si es obligatorio en tu modelo
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return {"message": "Usuario registrado correctamente", "user_id": nuevo_usuario.id}


# --- 2. LOGIN ---
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    
    user = db.query(User).filter(User.email == data.email).first()
    
    # (Nota: Aquí compararías el hash en la vida real)
    if not user or user.password != data.password:
        raise AppError("UNAUTHORIZED", "Credenciales incorrectas", 401)
        
    # Generar el Token inyectando el token_version actual
    payload = {
        "sub": str(user.id),
        "token_version": user.token_version,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    return {"access_token": token, "token_type": "bearer"}


# --- 3. LOGOUT (El que hicimos nosotros) ---
@router.post("/logout")
def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if db_user:
        # Esto invalida automáticamente el token actual
        db_user.token_version += 1
        db.commit()
    
    return {"detail": "Sesión cerrada correctamente. Token revocado."}