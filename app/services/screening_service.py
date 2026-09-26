from sqlalchemy.orm import Session

from app.models.screening import ScreeningAnswer


class ScreeningService:

    @staticmethod
    def save_answer(db: Session, candidate_id: int, call_id: int, question_key: str, answer: str) -> ScreeningAnswer:
        existing_answer = (db.query(ScreeningAnswer).filter(ScreeningAnswer.call_id == call_id, ScreeningAnswer.question_key == question_key).first())

        if existing_answer:
            existing_answer.answer = answer
            db.commit()
            db.refresh(existing_answer)
            return existing_answer
        
        screening_answer = ScreeningAnswer(
            candidate_id = candidate_id,
            call_id = call_id,
            question_key = question_key,
            answer = answer
        )

        db.add(screening_answer)
        db.commit()
        db.refresh(screening_answer)
        return screening_answer

    @staticmethod
    def get_answers(db: Session, call_id: int) -> dict[str, str]:
        answers = (db.query(ScreeningAnswer).filter(ScreeningAnswer.call_id == call_id).all())

        return {
            answer.question_key: answer.answer
            for answer in answers
        }