from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    SMS_MODE: str = "console"
    MSG91_API_KEY: str = ""
    MSG91_SENDER_ID: str = ""
    MSG91_DLT_TEMPLATE_ID: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
