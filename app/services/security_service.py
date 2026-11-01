import hashlib
import hmac
import secrets

from pwdlib import PasswordHash

from app.config import settings
from app.models.enums import OtpPurpose


password_hasher = PasswordHash.recommended()

# Used when an email does not exist, reducing timing differences.
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-that-is-never-valid")


class SecurityService:
    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def hash_password(password: str) -> str:
        return password_hasher.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str,) -> bool:
        try:
            return password_hasher.verify(password, password_hash,)
        except Exception:
            return False

    @staticmethod
    def generate_otp() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def hash_otp(*, user_id: int, purpose: OtpPurpose, otp: str,) -> str:
        secret = (settings.auth_otp_pepper.get_secret_value().encode("utf-8"))
        value = (f"{user_id}:{purpose.value}:{otp}".encode("utf-8"))
        return hmac.new(secret, value, hashlib.sha256,).hexdigest()

    @staticmethod
    def verify_otp(*, user_id: int, purpose: OtpPurpose, otp: str, expected_hash: str,) -> bool:
        calculated_hash = SecurityService.hash_otp(user_id=user_id, purpose=purpose, otp=otp,)
        return hmac.compare_digest(calculated_hash, expected_hash,)

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(48)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_ip_address(ip_address: str) -> str:
        secret = (settings.auth_ip_pepper.get_secret_value().encode("utf-8"))
        return hmac.new(secret, ip_address.encode("utf-8"), hashlib.sha256,).hexdigest()