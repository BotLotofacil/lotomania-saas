from sqlalchemy.orm import Session
from app.db import models
from app.core.security import hash_password, verify_password

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str):
    user = models.User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    sub = models.Subscription(user_id=user.id, active=False, plan="none")
    db.add(sub)
    db.commit()
    return user

def authenticate(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def has_active_subscription(db: Session, user_id: int) -> bool:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    return bool(sub and sub.active)
