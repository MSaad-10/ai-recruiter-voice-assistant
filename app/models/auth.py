from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import OtpPurpose

if TYPE_CHECKING:
    from app.models.user import User


class EmailVerificationOtp(Base):
    __tablename__ = "email_verification_otps"

    __table_args__ = (
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_email_verification_otps_attempt_count_positive",
        ),
        CheckConstraint(
            "max_attempts > 0",
            name="ck_email_verification_otps_max_attempts_positive",
        ),
        Index(
            "ix_email_verification_otps_lookup",
            "user_id",
            "purpose",
            "consumed_at",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,)
    purpose: Mapped[OtpPurpose] = mapped_column(
        SqlEnum(
            OtpPurpose,
            name="otp_purpose",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=OtpPurpose.EMAIL_VERIFICATION,
        server_default=OtpPurpose.EMAIL_VERIFICATION.value,
    )
    # Store an HMAC digest, never the six-digit OTP.
    otp_hash: Mapped[str] = mapped_column(String(64), nullable=False,)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0",)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5",)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True,)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),)
    user: Mapped["User"] = relationship(back_populates="verification_otps",)

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None


class UserSession(Base):
    __tablename__ = "user_sessions"

    __table_args__ = (
        Index(
            "ix_user_sessions_active_lookup",
            "user_id",
            "revoked_at",
            "expires_at",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,)

    # SHA-256 of a cryptographically random opaque session token.
    session_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True,)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True,)

    # A hash can be retained for security monitoring without storing raw IPs.
    ip_address_hash: Mapped[str | None] = mapped_column(String(64), nullable=True,)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True,)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),)
    user: Mapped["User"] = relationship(back_populates="sessions",)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False,)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    __table_args__ = (
        Index(
            "ix_password_reset_tokens_active_lookup",
            "user_id",
            "used_at",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,)

    # SHA-256 of a high-entropy random token.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True,)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True,)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),)
    user: Mapped["User"] = relationship(back_populates="password_reset_tokens",)