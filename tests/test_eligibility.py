from datetime import date
from app.models.candidate import Candidate

from app.eligibility.engine import EligibilityEngine


def candidate_with_age(age: int) -> Candidate:
    today = date.today()

    try:
        dob = today.replace(year=today.year - age)
    except ValueError:
        # Handles February 29.
        dob = today.replace(
            year=today.year - age,
            day=28,
        )

    return Candidate(dob=dob)


def valid_answers() -> dict[str, str]:
    return {
        "experience_years": "3",
        "work_authorized": "yes",
        "start_within_30_days": "yes",
        "full_time": "yes",
        "job_abandonment": "no",
        "education": "bachelor",
        "salary_acceptance": "yes",
        "language_fluent": "yes",
        "location_suitable": "yes",
        "working_hours": "yes",
        "interview_consent": "yes",
    }


def test_eligible_candidate_passes_all_rules():
    candidate = candidate_with_age(30)

    result = EligibilityEngine.evaluate(
        candidate=candidate,
        answers=valid_answers(),
    )

    assert result["eligible"] is True
    assert result["failed_rules"] == []


def test_insufficient_experience_fails():
    candidate = candidate_with_age(30)
    answers = valid_answers()
    answers["experience_years"] = "1"

    result = EligibilityEngine.evaluate(
        candidate=candidate,
        answers=answers,
    )

    assert result["eligible"] is False
    assert any(
        failure["rule"] == "minimum_experience"
        for failure in result["failed_rules"]
    )


def test_candidate_younger_than_21_fails():
    candidate = candidate_with_age(20)

    result = EligibilityEngine.evaluate(
        candidate=candidate,
        answers=valid_answers(),
    )

    assert result["eligible"] is False
    assert any(
        failure["rule"] == "age"
        for failure in result["failed_rules"]
    )


def test_candidate_older_than_55_fails():
    candidate = candidate_with_age(56)

    result = EligibilityEngine.evaluate(
        candidate=candidate,
        answers=valid_answers(),
    )

    assert result["eligible"] is False
    assert any(
        failure["rule"] == "age"
        for failure in result["failed_rules"]
    )