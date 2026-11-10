import pytest
from datetime import timedelta
from jose import jwt, ExpiredSignatureError, JWTError
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM

def test_password_hashing():
    password = "mypassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token_payload():
    data = {"sub": "fredy@example.com", "user_id": 1, "restaurant_id": 10}
    token = create_access_token(data=data)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "fredy@example.com"
    assert payload.get("user_id") == 1
    assert payload.get("restaurant_id") == 10
    assert "exp" in payload

def test_expired_access_token():
    data = {"sub": "fredy@example.com"}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=-5))
    
    with pytest.raises(ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def test_manipulated_invalid_token():
    data = {"sub": "fredy@example.com"}
    token = create_access_token(data=data)
    
    fake_token = token + "texto_inventado_para_hackear"
    
    with pytest.raises(JWTError):
        jwt.decode(fake_token, SECRET_KEY, algorithms=[ALGORITHM])