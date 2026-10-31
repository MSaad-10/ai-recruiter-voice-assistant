from fastapi import HTTPException

from app.models.call import Call
from app.models.candidate import Candidate


class AuthorizationService:
    @staticmethod
    def ensure_call_belongs_to_candidate(*, call:Call, candidate:Candidate) -> None:
        if call.candidate_id != candidate.id:
            raise HTTPException(
                status_code = 403,
                detail = "This voice session does not belong to the candidate.",
            )
