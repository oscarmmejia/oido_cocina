from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Esquema para validar los datos que envía el cliente al registrarse."""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Esquema para definir qué datos del usuario devolvemos (ocultando la contraseña)."""
    id: int
    email: EmailStr

    class Config:
        from_attributes = True