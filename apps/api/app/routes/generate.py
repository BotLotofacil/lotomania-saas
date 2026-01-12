from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, conint
from app.db.session import get_db
from app.core.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db import models, crud
from app.engine.lotomania import LotomaniaConfig, generate_lotomania_tickets
import json

router = APIRouter(prefix="/generate", tags=["generate"])
auth_scheme = HTTPBearer()

class GenerateIn(BaseModel):
    lottery: str = "lotomania"
    count: conint(ge=1, le=50)  # usuário escolhe
    window: conint(ge=20, le=200) = 50

def get_user_id(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    data = decode_token(creds.credentials)
    return int(data["sub"])

@router.post("")
def generate(payload: GenerateIn, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Paywall
    if not crud.has_active_subscription(db, user_id):
        raise HTTPException(status_code=402, detail="Assinatura necessária para gerar apostas.")

    if payload.lottery != "lotomania":
        raise HTTPException(status_code=400, detail="Por enquanto, apenas Lotomania.")

    # TODO: trocar por resultados reais (lidos de tabela draws)
    # Por agora, placeholders: último resultado e janela vazia
    base_draw_id = "last_draw_stub"
    last_draw_numbers = []  # Lotomania: 20 dezenas, mas aqui não é obrigatório no stub
    window_results = []     # lista de draws (cada draw = lista de ints)

    cfg = LotomaniaConfig(count=payload.count, window=payload.window)
    tickets, audits = generate_lotomania_tickets(
        user_id=user_id,
        base_draw_id=base_draw_id,
        last_draw_numbers=last_draw_numbers,
        window_results=window_results,
        cfg=cfg
    )

    sess = models.GenerationSession(user_id=user_id, lottery="lotomania", requested_count=payload.count)
    db.add(sess)
    db.commit()
    db.refresh(sess)

    out = []
    for i, (t, a) in enumerate(zip(tickets, audits), start=1):
        bet = models.Bet(
            session_id=sess.id,
            index=i,
            numbers_csv=",".join(f"{n:02d}" for n in t),
            audit_json=json.dumps(a, ensure_ascii=False),
        )
        db.add(bet)
        out.append({"index": i, "numbers": [f"{n:02d}" for n in t], "audit": a})

    db.commit()
    return {"session_id": sess.id, "bets": out}
