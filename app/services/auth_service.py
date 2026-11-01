from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import (EmailVerificationOtp, UserSession,)
from app.models.enums import OtpPurpose, UserRole
from app.models.user import User
from app.services.auth_exceptions import (EmailNotVerifiedError, InactiveAccountError, InvalidCredentialsError, InvalidOtpError,)
from app.services.security_service import (DUMMY_PASSWORD_HASH, SecurityService,)


GENERIC_VERIFICATION_MESSAGE = (
    "If the email can be verified, a verification code "
    "will be sent."
)


class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str,) -> User | None:
        normalized_email = SecurityService.normalize_email(email)
        return db.scalar(select(User).where(User.email == normalized_email))

    @staticmethod
    def signup(*, db: Session, email: str, password: str,) -> tuple[User, str | None]:
        normalized_email = SecurityService.normalize_email(email)

        existing_user = AuthService.get_user_by_email(db=db, email=normalized_email,)

        if existing_user:
            if (existing_user.is_active and not existing_user.is_email_verified):
                otp = AuthService.issue_verification_otp(db=db,user=existing_user,)
                return existing_user, otp

            # Keep the public response generic.
            return existing_user, None

        user = User(
            email=normalized_email,
            password_hash=SecurityService.hash_password(password),
            role=UserRole.CANDIDATE,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        otp = AuthService.issue_verification_otp(db=db, user=user,)

        return user, otp

    @staticmethod
    def issue_verification_otp(*, db: Session, user: User,) -> str | None:
        if not user.is_active or user.is_email_verified:
            return None

        now = datetime.now(timezone.utc)
        cooldown_start = now - timedelta(
            seconds=settings.auth_otp_resend_cooldown_seconds
        )
        hour_start = now - timedelta(hours=1)

        latest_otp = db.scalar(
            select(EmailVerificationOtp)
            .where(
                EmailVerificationOtp.user_id == user.id,
                EmailVerificationOtp.purpose
                == OtpPurpose.EMAIL_VERIFICATION,
            )
            .order_by(
                EmailVerificationOtp.created_at.desc()
            )
            .limit(1)
        )

        if (
            latest_otp
            and latest_otp.created_at >= cooldown_start
        ):
            return None

        otp_count = db.scalar(
            select(func.count())
            .select_from(EmailVerificationOtp)
            .where(
                EmailVerificationOtp.user_id == user.id,
                EmailVerificationOtp.purpose
                == OtpPurpose.EMAIL_VERIFICATION,
                EmailVerificationOtp.created_at >= hour_start,
            )
        )

        if otp_count >= settings.auth_otp_max_per_hour:
            return None

        # Invalidate every previous active OTP.
        db.execute(
            update(EmailVerificationOtp)
            .where(
                EmailVerificationOtp.user_id == user.id,
                EmailVerificationOtp.purpose
                == OtpPurpose.EMAIL_VERIFICATION,
                EmailVerificationOtp.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )

        raw_otp = SecurityService.generate_otp()

        verification_otp = EmailVerificationOtp(
            user_id=user.id,
            purpose=OtpPurpose.EMAIL_VERIFICATION,
            otp_hash=SecurityService.hash_otp(
                user_id=user.id,
                purpose=OtpPurpose.EMAIL_VERIFICATION,
                otp=raw_otp,
            ),
            attempt_count=0,
            max_attempts=5,
            expires_at=now
            + timedelta(
                minutes=settings.auth_otp_expiry_minutes
            ),
        )

        db.add(verification_otp)
        db.commit()

        return raw_otp

    @staticmethod
    def verify_email(
        *,
        db: Session,
        email: str,
        otp: str,
    ) -> User:
        user = AuthService.get_user_by_email(
            db=db,
            email=email,
        )

        if not user or not user.is_active:
            raise InvalidOtpError()

        if user.is_email_verified:
            return user

        verification_otp = db.scalar(
            select(EmailVerificationOtp)
            .where(
                EmailVerificationOtp.user_id == user.id,
                EmailVerificationOtp.purpose
                == OtpPurpose.EMAIL_VERIFICATION,
                EmailVerificationOtp.consumed_at.is_(None),
            )
            .order_by(
                EmailVerificationOtp.created_at.desc()
            )
            .limit(1)
        )

        now = datetime.now(timezone.utc)

        if not verification_otp:
            raise InvalidOtpError()

        if verification_otp.expires_at <= now:
            verification_otp.consumed_at = now
            db.commit()
            raise InvalidOtpError()

        if (
            verification_otp.attempt_count
            >= verification_otp.max_attempts
        ):
            verification_otp.consumed_at = now
            db.commit()
            raise InvalidOtpError()

        is_valid = SecurityService.verify_otp(
            user_id=user.id,
            purpose=OtpPurpose.EMAIL_VERIFICATION,
            otp=otp,
            expected_hash=verification_otp.otp_hash,
        )

        if not is_valid:
            verification_otp.attempt_count += 1

            if (
                verification_otp.attempt_count
                >= verification_otp.max_attempts
            ):
                verification_otp.consumed_at = now

            db.commit()
            raise InvalidOtpError()

        verification_otp.consumed_at = now
        user.email_verified_at = now

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def signin(
        *,
        db: Session,
        email: str,
        password: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[User, str, str]:
        user = AuthService.get_user_by_email(
            db=db,
            email=email,
        )

        password_hash = (
            user.password_hash
            if user
            else DUMMY_PASSWORD_HASH
        )

        valid_password = SecurityService.verify_password(
            password,
            password_hash,
        )

        if not user or not valid_password:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveAccountError()

        if not user.is_email_verified:
            raise EmailNotVerifiedError()

        now = datetime.now(timezone.utc)

        raw_session_token = SecurityService.generate_token()
        raw_csrf_token = SecurityService.generate_token()

        session = UserSession(
            user_id=user.id,
            session_token_hash=SecurityService.hash_token(
                raw_session_token
            ),
            csrf_token_hash=SecurityService.hash_token(
                raw_csrf_token
            ),
            user_agent=(
                user_agent[:500]
                if user_agent
                else None
            ),
            ip_address_hash=(
                SecurityService.hash_ip_address(ip_address)
                if ip_address
                else None
            ),
            expires_at=now
            + timedelta(
                days=settings.auth_session_days
            ),
            last_seen_at=now,
        )

        user.last_login_at = now

        # Remove already expired sessions.
        db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user.id,
                UserSession.expires_at <= now,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

        active_sessions = list(
            db.scalars(
                select(UserSession)
                .where(
                    UserSession.user_id == user.id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > now,
                )
                .order_by(UserSession.created_at.desc())
            )
        )

        # Reserve one position for the new session.
        sessions_to_keep = max(
            settings.auth_max_active_sessions - 1,
            0,
        )

        for old_session in active_sessions[sessions_to_keep:]:
            old_session.revoked_at = now

        db.add(session)
        db.commit()
        db.refresh(user)

        return (
            user,
            raw_session_token,
            raw_csrf_token,
        )

    @staticmethod
    def revoke_session(
        *,
        db: Session,
        session: UserSession,
    ) -> None:
        if session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()