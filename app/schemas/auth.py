from typing import Annotated
from pydantic import (BaseModel, EmailStr, Field, field_validator,)

from app.models.enums import UserRole


PasswordField = Annotated[str, Field(min_length=12, max_length=128),]

class SignupRequest(BaseModel):
    email: EmailStr
    password: PasswordField

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be blank.")

        return value


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class SigninRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class MessageResponse(BaseModel):
    message: str


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool
    is_email_verified: bool
    candidate_profile_id: int | None
    profile_completed: bool