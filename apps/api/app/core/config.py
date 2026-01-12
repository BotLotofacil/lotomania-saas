from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/lotomania"
    JWT_SECRET: str = "CHANGE_ME"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 60 * 24 * 7  # 7 dias

    STRIPE_ENABLED: bool = False
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_1M: str = ""
    STRIPE_PRICE_3M: str = ""
    STRIPE_PRICE_1Y: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

settings = Settings()
