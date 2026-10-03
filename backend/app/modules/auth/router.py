from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.schemas import (
    RegisterRequest,
    UserResponse,
    LoginRequest,
    TokenResponse,
)
from app.modules.auth.service import create_user, login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return create_user(db, body)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# login
@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        return login_user(
            db,
            body.email,
            body.password,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )
