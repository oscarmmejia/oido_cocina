from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate
from app.core.security import hash_password

def create_user(db: Session, user_data: UserCreate):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado en el sistema."
        )
    
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def assign_role_to_user(db: Session, user_id: int, role_id: int, restaurant_id: int):
    user = db.query(User).filter(User.id == user_id, User.restaurant_id == restaurant_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found in this restaurant"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Role not found"
        )
        
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
        
    return user

def revoke_role_from_user(db: Session, user_id: int, role_id: int, restaurant_id: int):
    user = db.query(User).filter(User.id == user_id, User.restaurant_id == restaurant_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found in this restaurant"
        )

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Role not found"
        )
        
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
        
    return user