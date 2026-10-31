from enum import Enum


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    ADMIN = "admin"

class OtpPurpose(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
