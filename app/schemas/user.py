from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Esquema para validar los datos que envía el cliente al registrarse."""
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    password: str
    

class UserResponse(BaseModel):
    """Esquema para definir qué datos del usuario devolvemos (ocultando la contraseña)."""
    id: int
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role_id: int
    restaurant_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True