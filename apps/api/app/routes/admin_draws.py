from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.core.security import decode_token
from app.db import models
import re

router = APIRouter(prefix="/admin", tags=["admin"])
auth_scheme = HTTPBearer()

# simples: primeiro usuário (id=1) vira "admin"
def require_admin(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> int:
    data = decode_token(creds.credentials)
    uid = int(data["sub"])
    if uid != 1:
        raise HTTPException(status_code=403, detail="Somente admin.")
    return uid

class ImportIn(BaseModel):
    lottery: str = "lotomania"
    raw_text: str

def parse_draws(raw_text: str):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    out = []
    for line in lines:
        m = re.match(r"(\d+)\s*-\s*([\d/]+)\s*-\s*(.+)$", line)
        if not m:
            continue
        contest = int(m.group(1))
        date_br = m.group(2).strip()
        nums = [int(x) for x in m.group(3).split()]
        if len(nums) != 20:
            raise ValueError(f"Concurso {contest}: esperado 20 dezenas, veio {len(nums)}")
        nums_csv = ",".join(f"{n:02d}" for n in sorted(nums))
        out.append((contest, date_br, nums_csv))
    return out

@router.post("/import-draws")
def import_draws(payload: ImportIn, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    if payload.lottery != "lotomania":
        raise HTTPException(status_code=400, detail="Por enquanto só Lotomania.")

    try:
        draws = parse_draws(payload.raw_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # upsert simples: se existir, atualiza; se não, cria
    inserted = 0
    updated = 0
    for contest, date_br, nums_csv in draws:
        row = db.query(models.Draw).filter(models.Draw.contest == contest).first()
        if row:
            row.date_br = date_br
            row.numbers_csv = nums_csv
            updated += 1
        else:
            db.add(models.Draw(lottery="lotomania", contest=contest, date_br=date_br, numbers_csv=nums_csv))
            inserted += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "total_received": len(draws)}
