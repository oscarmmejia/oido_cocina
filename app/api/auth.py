from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.core.database_connection import get_db
from app.schemas.user import UserResponse
from app.core.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM


from app.models.security_model import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id = payload.get("user_id")
        token_version = payload.get("token_version")

        if (
            not isinstance(email, str) or not email
            or type(user_id) is not int or user_id <= 0
            or type(token_version) is not int or token_version < 0
            or "restaurant_id" not in payload or "exp" not in payload
        ):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, user_id, populate_existing=True)
    if user is None or user.email != email or user.token_version != token_version:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario está inactiva."
        )

    return user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El correo electrónico o la contraseña no son correctos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de usuario está inactiva."
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "restaurant_id": user.restaurant_id,
            "token_version": user.token_version,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
