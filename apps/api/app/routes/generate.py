from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, conint
import json

from app.db.session import get_db
from app.core.security import decode_token
from app.db import models, crud

router = APIRouter(prefix="/generate", tags=["generate"])
auth_scheme = HTTPBearer()


class GenerateIn(BaseModel):
    lottery: str = "lotomania"
    count: conint(ge=1, le=50)                 # usuário escolhe
    window: conint(ge=20, le=200) = 60         # agora padrão 60 (você pediu janela 60)


def get_user_id(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    data = decode_token(creds.credentials)
    return int(data["sub"])


@router.post("")
def generate(
    payload: GenerateIn,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id),
):
    # Paywall
    if not crud.has_active_subscription(db, user_id):
        raise HTTPException(
            status_code=402,
            detail="Assinatura necessária para gerar apostas."
        )

    if payload.lottery != "lotomania":
        raise HTTPException(
            status_code=400,
            detail="Por enquanto, apenas Lotomania."
        )

    # 1) Puxa os últimos "window" concursos do banco (desc)
    window = int(payload.window)

    rows = (
        db.query(models.Draw)
        .filter(models.Draw.lottery == "lotomania")
        .order_by(models.Draw.contest.desc())
        .limit(window)
        .all()
    )

    # proteção: motor pede histórico real mínimo (ajuste se você quiser outro corte)
    if len(rows) < 20:
        raise HTTPException(
            status_code=400,
            detail="Poucos resultados no banco. Importe os concursos primeiro."
        )

    # 2) Base draw = concurso mais recente
    base_draw_id = str(rows[0].contest)

    # 3) Monta window_results a partir do numbers_csv
    window_results = []
    for r in rows:
        if not r.numbers_csv:
            continue
        nums = [int(x) for x in r.numbers_csv.split(",") if x != ""]
        window_results.append(nums)

    if len(window_results) < 20:
        raise HTTPException(
            status_code=400,
            detail="Resultados inválidos no banco (numbers_csv vazio/ruim)."
        )

    # 4) Chama o motor
    from app.engine.lotomania import LotomaniaConfig, generate_lotomania_tickets

    cfg = LotomaniaConfig(count=payload.count, window=window)

    # OBS: aqui você pode decidir se passa last_draw_numbers também.
    # Se o seu motor NÃO precisa, deixe assim.
    tickets, audits = generate_lotomania_tickets(
        user_id=user_id,
        base_draw_id=base_draw_id,
        window_results=window_results,
        cfg=cfg
    )

    # 5) Cria sessão de geração
    sess = models.GenerationSession(
        user_id=user_id,
        lottery="lotomania",
        requested_count=payload.count
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    # 6) Salva apostas e devolve payload
    out = []
    for i, (t, a) in enumerate(zip(tickets, audits), start=1):
        bet = models.Bet(
            session_id=sess.id,
            index=i,
            numbers_csv=",".join(f"{n:02d}" for n in t),
            audit_json=json.dumps(a, ensure_ascii=False),
        )
        db.add(bet)
        out.append({
            "index": i,
            "numbers": [f"{n:02d}" for n in t],
            "audit": a
        })

    db.commit()
    return {"session_id": sess.id, "bets": out}
