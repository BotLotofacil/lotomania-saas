from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.core.config import settings
from app.db import models
import stripe
from datetime import datetime

router = APIRouter(prefix="/billing", tags=["billing"])
auth_scheme = HTTPBearer()

def get_user_id(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    data = decode_token(creds.credentials)
    return int(data["sub"])

@router.get("/plans")
def plans():
    return {
        "enabled": settings.STRIPE_ENABLED,
        "plans": [
            {"id": "1m", "label": "1 mês"},
            {"id": "3m", "label": "3 meses"},
            {"id": "1y", "label": "1 ano"},
        ],
    }

@router.post("/checkout")
def checkout(plan_id: str, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    if not settings.STRIPE_ENABLED:
        raise HTTPException(status_code=400, detail="Stripe ainda não habilitado no servidor.")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    price_map = {"1m": settings.STRIPE_PRICE_1M, "3m": settings.STRIPE_PRICE_3M, "1y": settings.STRIPE_PRICE_1Y}
    if plan_id not in price_map or not price_map[plan_id]:
        raise HTTPException(status_code=400, detail="Plano/Price inválido no Stripe.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if not user or not sub:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email)
        sub.stripe_customer_id = customer["id"]
        db.commit()

    session = stripe.checkout.Session.create(
        customer=sub.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_map[plan_id], "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/assinatura?success=1",
        cancel_url=f"{settings.FRONTEND_URL}/assinatura?canceled=1",
    )
    return {"url": session["url"]}

@router.post("/webhook")
async def webhook(req: Request, db: Session = Depends(get_db)):
    if not settings.STRIPE_ENABLED:
        raise HTTPException(status_code=400, detail="Stripe desabilitado.")

    payload = await req.body()
    sig = req.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook inválido.")

    # Evento principal: subscription updated/created
    if event["type"] in ("customer.subscription.created", "customer.subscription.updated"):
        sub_obj = event["data"]["object"]
        customer_id = sub_obj["customer"]
        stripe_sub_id = sub_obj["id"]
        status = sub_obj["status"]
        current_period_end = datetime.utcfromtimestamp(sub_obj["current_period_end"]).isoformat()

        sub = db.query(models.Subscription).filter(models.Subscription.stripe_customer_id == customer_id).first()
        if sub:
            sub.stripe_subscription_id = stripe_sub_id
            sub.active = status in ("active", "trialing")
            sub.current_period_end = current_period_end
            db.commit()

    return {"ok": True}
