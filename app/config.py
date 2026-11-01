from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import EmailStr, SecretStr

class Settings(BaseSettings):
    database_url: str

    vapi_api_key: str
    vapi_squad_id: str

    app_environment: Literal["development", "test", "production",] = "development"
    
    frontend_url: str = "http://127.0.0.1:5173"

    auth_otp_pepper: SecretStr
    auth_ip_pepper: SecretStr

    auth_otp_expiry_minutes: int = 10
    auth_otp_resend_cooldown_seconds: int = 60
    auth_otp_max_per_hour: int = 5
    auth_session_days: int = 7
    auth_max_active_sessions: int = 5

    auth_session_cookie_name: str = "ai_recruiter_session"
    auth_csrf_cookie_name: str = "ai_recruiter_csrf"
    auth_cookie_domain: str | None = None

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: EmailStr
    smtp_from_name: str = "NeuroOceans AI Recruiter"
    smtp_start_tls: bool = True

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf_8",
    )

settings = Settings()