from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./billing.db"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "billing@example.com"
    smtp_use_tls: bool = True

    app_name: str = "Billing System"
    currency_symbol: str = "Rs."
    default_denomination_values: tuple[int, ...] = (500, 50, 20, 10, 5, 2, 1)


settings = Settings()
