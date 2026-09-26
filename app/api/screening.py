from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.screening import (
    SaveScreeningAnswerResponse,
    SaveScreeningAnswerRequest,
    EligibilityRequest,
    EligibilityResponse
)
from app.services.candidate_service import CandidateService
from app.services.call_service import CallService
from app.services.screening_service import ScreeningService
from app.eligibility.engine import EligibilityEngine


router = APIRouter(
    prefix="/tools",
    tags=["Vapi Tools"]
)


@router.post("/save-screening-answer", response_model=SaveScreeningAnswerResponse)
def save_screening_answer(data: SaveScreeningAnswerRequest, db: Session = Depends(get_db)):
    candidate = CandidateService.get_candidate(db=db, candidate_id=data.candidate_id)

    if not candidate:
        raise HTTPException(status_code = 404, detail = "Candidate not found")
    
    call = CallService.get_call(db=db, call_id=data.call_id)

    if not call:
        raise HTTPException(status_code = 404, detail = "Voice session not found")
    
    ScreeningService.save_answer(
        db=db,
        candidate_id=data.candidate_id,
        call_id=data.call_id,
        question_key=data.question_key,
        answer=data.answer
    )

    return SaveScreeningAnswerResponse(saved=True, message="Screening answer saved successfully.")


@router.post("/check-eligibility", response_model=EligibilityResponse)
def check_eligibility(data: EligibilityRequest, db: Session = Depends(get_db)):
    candidate = CandidateService.get_candidate(db=db, candidate_id=data.candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    call = CallService.get_call(db=db, call_id=data.call_id)

    if not call:
        raise HTTPException(status_code=404, detail="Voice session not found")
    
    answers = ScreeningService.get_answers(db=db, call_id=data.call_id)

    result = EligibilityEngine.evaluate(candidate=candidate, answers=answers)

    if result["eligible"]:
        CallService.update_status(db=db, call=call, status="Eligible")
    
    else:
        CallService.update_status(db=db, call=call, status="NotEligible")

    return EligibilityResponse(
        eligible=result["eligible"],
        failed_rules=result["failed_rules"]
    )