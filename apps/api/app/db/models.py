from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subscription: Mapped["Subscription"] = relationship(back_populates="user", uselist=False)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    plan: Mapped[str] = mapped_column(String(50), default="none")  # "1m"|"3m"|"1y"
    stripe_customer_id: Mapped[str] = mapped_column(String(255), default="")
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), default="")
    current_period_end: Mapped[str] = mapped_column(String(50), default="")  # ISO string

    user: Mapped["User"] = relationship(back_populates="subscription")

class GenerationSession(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lottery: Mapped[str] = mapped_column(String(50))  # "lotomania"
    requested_count: Mapped[int] = mapped_column(Integer)

class Bet(Base):
    __tablename__ = "bets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    index: Mapped[int] = mapped_column(Integer)  # 1..N
    numbers_csv: Mapped[str] = mapped_column(String(400))  # "00,01,..."
    audit_json: Mapped[str] = mapped_column(Text)  # JSON string
