import pytest
from jose import jwt
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM

def test_hash_and_verify_password():
    password = "password_super_seguro"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("clave_equivocada", hashed) is False

def test_create_access_token():
    data = {"sub": "usuario_test"}
    token = create_access_token(data=data)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "usuario_test"
    assert "exp" in payload