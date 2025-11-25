# app/auth/repository.py
from sqlalchemy.orm import Session
from app.users.models import User
from app.auth.security import hash_password, verify_password, create_access_token

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def register_user(db: Session, email: str, password: str):
    if get_user_by_email(db, email):
        raise ValueError("user_exists")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_token_for_user(user: User):
    return create_access_token(subject=str(user.id))
