from pydantic import BaseModel


class SaveScreeningAnswerRequest(BaseModel):
    candidate_id: int
    call_id: int
    question_key: str
    answer: str


class SaveScreeningAnswerResponse(BaseModel):
    saved: bool
    message: str


class EligibilityRequest(BaseModel):
    candidate_id: int
    call_id: int


class FailedRule(BaseModel):
    rule: str
    reason: str


class EligibilityResponse(BaseModel):
    eligible: bool
    failed_rules: list[FailedRule]
