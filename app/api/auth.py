import logging

from fastapi import (APIRouter, Depends, HTTPException, Request, Response, status,)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (CurrentUserResponse, MessageResponse, ResendVerificationRequest, SigninRequest, SignupRequest, VerifyEmailRequest,)
from app.services.auth_exceptions import (EmailNotVerifiedError, InactiveAccountError, InvalidCredentialsError, InvalidOtpError,)
from app.services.auth_service import (AuthService, GENERIC_VERIFICATION_MESSAGE,)
from app.services.cookie_service import CookieService
from app.services.email_service import EmailService
from app.services.auth_dependencies import (AuthContext, get_current_user, require_csrf,)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def serialize_user(user: User) -> CurrentUserResponse:
    profile = user.candidate_profile

    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        candidate_profile_id=(
            profile.id if profile else None
        ),
        profile_completed=bool(
            profile and profile.profile_completed_at
        ),
    )


@router.post("/signup", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED,)
async def signup(data: SignupRequest, db: Session = Depends(get_db),):
    user, otp = AuthService.signup(
        db=db,
        email=str(data.email),
        password=data.password,
    )

    if otp:
        try:
            await EmailService.send_verification_otp(
                recipient=user.email,
                otp=otp,
            )
        except Exception:
            logger.exception(
                "Verification email delivery failed "
                "for user_id=%s",
                user.id,
            )

            raise HTTPException(
                status_code=503,
                detail=(
                    "The account was created, but the "
                    "verification email could not be sent. "
                    "Please try resending it."
                ),
            )

    return MessageResponse(
        message=GENERIC_VERIFICATION_MESSAGE
    )


@router.post("/resend-verification", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED,)
async def resend_verification(data: ResendVerificationRequest, db: Session = Depends(get_db),):
    user = AuthService.get_user_by_email(
        db=db,
        email=str(data.email),
    )

    otp = None

    if user:
        otp = AuthService.issue_verification_otp(
            db=db,
            user=user,
        )

    if user and otp:
        try:
            await EmailService.send_verification_otp(
                recipient=user.email,
                otp=otp,
            )
        except Exception:
            logger.exception(
                "Verification email resend failed "
                "for user_id=%s",
                user.id,
            )

    # Always return the same response.
    return MessageResponse(message=GENERIC_VERIFICATION_MESSAGE)


@router.post("/verify-email", response_model=MessageResponse,)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db),):
    try:
        AuthService.verify_email(
            db=db,
            email=str(data.email),
            otp=data.otp,
        )
    except InvalidOtpError:
        raise HTTPException(
            status_code=400,
            detail="The verification code is invalid or expired.",
        )

    return MessageResponse(
        message="Email verified successfully. You can now sign in."
    )


@router.post("/signin", response_model=CurrentUserResponse,)
def signin(data: SigninRequest, request: Request, response: Response, db: Session = Depends(get_db),):
    try:
        user, session_token, csrf_token = AuthService.signin(
            db=db,
            email=str(data.email),
            password=data.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )
    except EmailNotVerifiedError:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "email_not_verified",
                "message": "Verify your email before signing in.",
            },
        )
    except InactiveAccountError:
        raise HTTPException(
            status_code=403,
            detail="This account is not active.",
        )

    CookieService.set_auth_cookies(
        response=response,
        session_token=session_token,
        csrf_token=csrf_token,
    )

    return serialize_user(user)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT,)
def signout(response: Response, auth: AuthContext = Depends(require_csrf), db: Session = Depends(get_db),):
    AuthService.revoke_session(
        db=db,
        session=auth.session,
    )

    CookieService.clear_auth_cookies(response)


@router.get("/me", response_model=CurrentUserResponse,)
def get_me(user: User = Depends(get_current_user),):
    return serialize_user(user)