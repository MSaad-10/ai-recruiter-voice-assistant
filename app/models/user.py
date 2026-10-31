from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (Boolean, DateTime, Enum as SqlEnum, String, func, true,)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole


if TYPE_CHECKING:
    from app.models.auth import (EmailVerificationOtp, PasswordResetToken, UserSession,)
    from app.models.candidate import Candidate 

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True,)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        nullable=False,
        default=UserRole.CANDIDATE,
        server_default=UserRole.CANDIDATE.value,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true(), index=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True,)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(),)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(),)
    candidate_profile: Mapped["CandidateProfile | None"] = relationship(back_populates="user", uselist=False, passive_deletes=True,)
    verification_otps: Mapped[list["EmailVerificationOtp"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True,)
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True,)
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True,)

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
