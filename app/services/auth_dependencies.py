from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models.auth import UserSession
from app.models.user import User
from app.services.security_service import SecurityService


@dataclass
class AuthContext:
    user: User
    session: UserSession


def get_auth_context(request: Request, db: Session = Depends(get_db),) -> AuthContext:
    raw_token = request.cookies.get(settings.auth_session_cookie_name)

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    token_hash = SecurityService.hash_token(raw_token)
    now = datetime.now(timezone.utc)

    session = db.scalar(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(
            UserSession.session_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )

    if not session or not session.user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session.",
        )

    # Avoid writing to the database on every request.
    if session.last_seen_at < now - timedelta(minutes=5):
        session.last_seen_at = now
        db.commit()

    return AuthContext(
        user=session.user,
        session=session,
    )


def get_current_user(auth: AuthContext = Depends(get_auth_context),) -> User:
    return auth.user


def require_csrf(request: Request, auth: AuthContext = Depends(get_auth_context),) -> AuthContext:
    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get(
        settings.auth_csrf_cookie_name
    )

    if not csrf_header or not csrf_cookie:
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed.",
        )

    if csrf_header != csrf_cookie:
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed.",
        )

    supplied_hash = SecurityService.hash_token(
        csrf_header
    )

    if supplied_hash != auth.session.csrf_token_hash:
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed.",
        )

    return auth