from fastapi import FastAPI
from app.db.session import engine, Base
from app.routes.auth import router as auth_router
from app.routes.generate import router as gen_router
from app.routes.billing import router as billing_router
from app.routes.admin_draws import router as admin_router

app = FastAPI(title="Lotomania SaaS API")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(gen_router)
app.include_router(billing_router)
app.include_router(admin_router)

@app.get("/health")
def health():
    return {"status": "ok"}
