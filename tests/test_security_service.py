from app.models.enums import OtpPurpose
from app.services.security_service import SecurityService


def test_password_hash_does_not_store_password():
    password = "a-secure-test-passphrase"

    password_hash = SecurityService.hash_password(password)

    assert password_hash != password
    assert SecurityService.verify_password(password, password_hash,)


def test_wrong_password_fails():
    password_hash = SecurityService.hash_password("correct-test-password")
    assert not SecurityService.verify_password("wrong-test-password", password_hash,)


def test_otp_hash_is_deterministic_for_verification():
    first_hash = SecurityService.hash_otp(
        user_id=1,
        purpose=OtpPurpose.EMAIL_VERIFICATION,
        otp="123456",
    )

    second_hash = SecurityService.hash_otp(
        user_id=1,
        purpose=OtpPurpose.EMAIL_VERIFICATION,
        otp="123456",
    )

    assert first_hash == second_hash


def test_otp_hash_is_bound_to_user():
    first_hash = SecurityService.hash_otp(
        user_id=1,
        purpose=OtpPurpose.EMAIL_VERIFICATION,
        otp="123456",
    )

    second_hash = SecurityService.hash_otp(
        user_id=2,
        purpose=OtpPurpose.EMAIL_VERIFICATION,
        otp="123456",
    )

    assert first_hash != second_hash


def test_session_tokens_are_random():
    first_token = SecurityService.generate_token()
    second_token = SecurityService.generate_token()

    assert first_token != second_token
    assert len(first_token) >= 40