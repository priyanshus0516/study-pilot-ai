from typing import List, Dict, Any, Optional
from database.database import db
from database.models import Quiz, QuizQuestion, Document, StudyActivity
from services.ai_service import AIService

class QuizService:
    def __init__(self):
        self.ai_service = AIService()

    def create_quiz_from_document(
        self,
        user_id: int,
        document_id: Optional[int],
        topic: str,
        difficulty: str = "Medium",
        num_questions: int = 5
    ) -> Quiz:
        """
        Creates a new quiz, generates questions using AI, and saves to database.
        """
        context_text = ""
        doc_name = topic
        if document_id:
            doc = Document.query.filter_by(id=document_id, user_id=user_id).first()
            if doc:
                doc_name = doc.filename
                # Assemble text from chunks
                context_text = " ".join([c.chunk_text for c in doc.chunks[:10]])

        if not context_text:
            context_text = f"Study notes and principles covering {topic} for university examinations and software engineering."

        # Generate questions via AI
        generated_questions = self.ai_service.generate_quiz(
            text=context_text,
            topic=topic or doc_name,
            difficulty=difficulty,
            num_questions=num_questions
        )

        quiz = Quiz(
            user_id=user_id,
            document_id=document_id,
            topic=topic or doc_name,
            difficulty=difficulty,
            score=0,
            total_questions=len(generated_questions),
            completed=False
        )
        db.session.add(quiz)
        db.session.flush()

        for q_data in generated_questions:
            # Handle option dictionaries or fields
            opts = q_data.get('options', {})
            opt_a = opts.get('A', q_data.get('option_a', ''))
            opt_b = opts.get('B', q_data.get('option_b', ''))
            opt_c = opts.get('C', q_data.get('option_c', ''))
            opt_d = opts.get('D', q_data.get('option_d', ''))
            correct = q_data.get('correct_answer', 'A').upper().strip()
            if correct not in ['A', 'B', 'C', 'D']:
                correct = 'A'

            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data.get('question', 'Question'),
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                correct_answer=correct,
                explanation=q_data.get('explanation', '')
            )
            db.session.add(qq)

        # Log study activity
        activity = StudyActivity(
            user_id=user_id,
            activity_type='quiz_generated',
            duration=5,
            details=f"Created {difficulty} quiz on {quiz.topic}"
        )
        db.session.add(activity)
        db.session.commit()

        return quiz

    def submit_quiz_answers(self, quiz_id: int, user_id: int, answers: Dict[int, str]) -> Dict[str, Any]:
        """
        Calculates score, marks answers, updates Quiz record and returns detailed analysis.
        answers is a dict: {question_id: 'A' | 'B' | 'C' | 'D'}
        """
        quiz = Quiz.query.filter_by(id=quiz_id, user_id=user_id).first()
        if not quiz:
            raise ValueError("Quiz not found")

        score = 0
        correct_count = 0
        incorrect_count = 0
        detailed_results = []

        for q in quiz.questions:
            user_ans = answers.get(q.id, answers.get(str(q.id), "")).strip().upper()
            q.selected_answer = user_ans
            is_correct = (user_ans == q.correct_answer)
            if is_correct:
                score += 1
                correct_count += 1
            else:
                incorrect_count += 1

            detailed_results.append({
                "id": q.id,
                "question": q.question,
                "selected": user_ans,
                "correct": q.correct_answer,
                "is_correct": is_correct,
                "explanation": q.explanation
            })

        quiz.score = score
        quiz.completed = True

        # Log completion
        activity = StudyActivity(
            user_id=user_id,
            activity_type='quiz_completed',
            duration=10,
            details=f"Completed {quiz.topic} quiz ({score}/{quiz.total_questions})"
        )
        db.session.add(activity)
        db.session.commit()

        percentage = round((score / quiz.total_questions * 100) if quiz.total_questions > 0 else 0, 1)
        weak_topic = quiz.topic if percentage < 70 else None

        return {
            "quiz_id": quiz.id,
            "topic": quiz.topic,
            "score": score,
            "total_questions": quiz.total_questions,
            "percentage": percentage,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "weak_topic": weak_topic,
            "results": detailed_results
        }
