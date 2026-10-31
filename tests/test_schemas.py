from app.schemas.scheduling import BookInterviewResponse


def test_unavailable_slot_response_allows_missing_interview():
    response = BookInterviewResponse(
        booked=False,
        message="The selected interview slot is no longer available.",
        interview_id=None,
        slot_id=7,
    )

    assert response.booked is False
    assert response.interview_id is None
    assert response.slot_id == 7