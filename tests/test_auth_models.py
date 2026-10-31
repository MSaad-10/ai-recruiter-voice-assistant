from app.models.enums import OtpPurpose, UserRole
from app.models.user import User
from app.models.candidate import CandidateProfile


def test_new_user_has_candidate_role():
    user = User(
        email="candidate@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.CANDIDATE,
    )

    assert user.role == UserRole.CANDIDATE


def test_email_verification_is_false_without_timestamp():
    user = User(
        email="candidate@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.CANDIDATE,
    )

    assert user.is_email_verified is False


def test_candidate_compatibility_alias():
    from app.models.candidate import Candidate

    assert Candidate is CandidateProfile


def test_otp_purpose_value():
    assert (OtpPurpose.EMAIL_VERIFICATION.value == "email_verification")