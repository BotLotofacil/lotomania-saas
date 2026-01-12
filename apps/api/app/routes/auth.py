from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.db import crud
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    user = crud.create_user(db, payload.email, payload.password)
    token = create_access_token(sub=str(user.id))
    return {"token": token}

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = crud.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    token = create_access_token(sub=str(user.id))
    return {"token": token}
