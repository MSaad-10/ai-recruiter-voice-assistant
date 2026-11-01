from fastapi import Response

from app.config import settings


class CookieService:
    @staticmethod
    def set_auth_cookies(*, response: Response, session_token: str, csrf_token: str,) -> None:
        max_age = settings.auth_session_days * 24 * 60 * 60
        secure = settings.app_environment != "development"

        response.set_cookie(
            key=settings.auth_session_cookie_name,
            value=session_token,
            max_age=max_age,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
            domain=settings.auth_cookie_domain,
        )

        response.set_cookie(
            key=settings.auth_csrf_cookie_name,
            value=csrf_token,
            max_age=max_age,
            httponly=False,
            secure=secure,
            samesite="lax",
            path="/",
            domain=settings.auth_cookie_domain,
        )

    @staticmethod
    def clear_auth_cookies(response: Response,) -> None:
        response.delete_cookie(
            key=settings.auth_session_cookie_name,
            path="/",
            domain=settings.auth_cookie_domain,
        )

        response.delete_cookie(
            key=settings.auth_csrf_cookie_name,
            path="/",
            domain=settings.auth_cookie_domain,
        )