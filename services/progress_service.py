from typing import Dict, Any, List
from sqlalchemy import func
from database.database import db
from database.models import User, Document, QuestionHistory, Quiz, Flashcard, StudyActivity

class ProgressService:
    @staticmethod
    def get_user_dashboard_stats(user_id: int) -> Dict[str, Any]:
        """
        Calculates all key metrics for the user's dashboard and progress view.
        """
        # Document count
        doc_count = Document.query.filter_by(user_id=user_id).count()

        # Questions asked
        questions_count = QuestionHistory.query.filter_by(user_id=user_id).count()

        # Quizzes
        completed_quizzes = Quiz.query.filter_by(user_id=user_id, completed=True).all()
        quiz_attempts = len(completed_quizzes)
        
        if quiz_attempts > 0:
            total_score_sum = sum(q.score for q in completed_quizzes)
            total_possible = sum(q.total_questions for q in completed_quizzes)
            avg_quiz_score = round((total_score_sum / total_possible * 100) if total_possible > 0 else 0, 1)
        else:
            avg_quiz_score = 0.0

        # Flashcards
        total_flashcards = Flashcard.query.filter_by(user_id=user_id).count()
        learned_flashcards = Flashcard.query.filter_by(user_id=user_id, is_learned=True).count()

        # Study Time (duration in minutes)
        total_minutes = db.session.query(func.coalesce(func.sum(StudyActivity.duration), 0))\
            .filter(StudyActivity.user_id == user_id).scalar()
        study_hours = round(total_minutes / 60, 1)

        # Topic Breakdown and Weak Topic Detection
        topic_scores: Dict[str, List[float]] = {}
        for q in completed_quizzes:
            t = q.topic.strip()
            pct = (q.score / q.total_questions * 100) if q.total_questions > 0 else 0
            if t not in topic_scores:
                topic_scores[t] = []
            topic_scores[t].append(pct)

        topic_stats = []
        weak_topics = []
        for topic, scores in topic_scores.items():
            avg = round(sum(scores) / len(scores), 1)
            topic_stats.append({
                "topic": topic,
                "average": avg,
                "attempts": len(scores),
                "is_weak": avg < 70
            })
            if avg < 70:
                weak_topics.append({
                    "topic": topic,
                    "score": avg,
                    "suggestion": f"You scored {avg}% in {topic}. Consider reviewing this topic."
                })

        # Sort topics descending by score
        topic_stats.sort(key=lambda x: x["average"], reverse=True)

        # If no quizzes completed yet, provide illustrative guide benchmarks
        if not topic_stats and doc_count > 0:
            user_docs = Document.query.filter_by(user_id=user_id).all()
            for doc in user_docs[:3]:
                topic_name = doc.filename.rsplit('.', 1)[0]
                weak_topics.append({
                    "topic": topic_name,
                    "score": 0,
                    "suggestion": f"New document uploaded: {topic_name}. Test your knowledge with a quick quiz!"
                })

        # Recent activities
        recent_activities = StudyActivity.query.filter_by(user_id=user_id)\
            .order_by(StudyActivity.created_at.desc()).limit(8).all()

        # Recent documents
        recent_documents = Document.query.filter_by(user_id=user_id)\
            .order_by(Document.uploaded_at.desc()).limit(5).all()

        return {
            "total_documents": doc_count,
            "questions_asked": questions_count,
            "quiz_attempts": quiz_attempts,
            "avg_quiz_score": avg_quiz_score,
            "total_flashcards": total_flashcards,
            "learned_flashcards": learned_flashcards,
            "study_hours": study_hours,
            "study_minutes": total_minutes,
            "topic_stats": topic_stats,
            "weak_topics": weak_topics,
            "recent_activities": [a.to_dict() for a in recent_activities],
            "recent_documents": [d.to_dict() for d in recent_documents]
        }
