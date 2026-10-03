from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.modules.auth.security import (
    hash_password,
    create_access_token,
    verify_password,
)
from app.modules.auth.schemas import RegisterRequest


def create_user(db: Session, data: RegisterRequest):

    name = data.name.strip()
    if not name or len(name) > 100:
        raise ValueError("Name must contain between 1 and 100 characters")
    if not data.password or len(data.password.encode("utf-8")) > 72:
        raise ValueError("Password must contain between 1 and 72 UTF-8 bytes")

    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        raise ValueError("Email already registered")

    user = User(name=name, email=data.email, password_hash=hash_password(data.password))

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Another registration may win after the initial existence check.
        if db.query(User).filter(User.email == data.email).first() is not None:
            raise ValueError("Email already registered") from None
        raise
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
):

    if not password or len(password.encode("utf-8")) > 72:
        return None

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
):

    user = authenticate_user(db, email, password)

    if not user:
        raise ValueError("Invalid credentials")

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }
