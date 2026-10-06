from typing import List, Dict, Any, Optional
from database.database import db
from database.models import Flashcard, Document, StudyActivity
from services.ai_service import AIService

class FlashcardService:
    def __init__(self):
        self.ai_service = AIService()

    def generate_cards_from_document(
        self,
        user_id: int,
        document_id: Optional[int],
        topic: str,
        count: int = 6
    ) -> List[Flashcard]:
        """
        Generates flashcards from document text using AI and saves to database.
        """
        context_text = ""
        topic_name = topic
        if document_id:
            doc = Document.query.filter_by(id=document_id, user_id=user_id).first()
            if doc:
                topic_name = topic or doc.filename.rsplit('.', 1)[0]
                context_text = " ".join([c.chunk_text for c in doc.chunks[:10]])

        if not context_text:
            context_text = f"Key terms and revision questions regarding {topic_name}."

        raw_cards = self.ai_service.generate_flashcards(
            text=context_text,
            topic=topic_name,
            count=count
        )

        created_cards = []
        for c in raw_cards:
            card = Flashcard(
                user_id=user_id,
                document_id=document_id,
                topic=c.get('topic', topic_name),
                question=c.get('question', 'Question'),
                answer=c.get('answer', 'Answer'),
                is_learned=False
            )
            db.session.add(card)
            created_cards.append(card)

        # Log activity
        activity = StudyActivity(
            user_id=user_id,
            activity_type='flashcards_created',
            duration=5,
            details=f"Generated {len(created_cards)} flashcards on {topic_name}"
        )
        db.session.add(activity)
        db.session.commit()

        return created_cards

    def create_card_manually(self, user_id: int, topic: str, question: str, answer: str) -> Flashcard:
        card = Flashcard(
            user_id=user_id,
            topic=topic.strip() or "General",
            question=question.strip(),
            answer=answer.strip(),
            is_learned=False
        )
        db.session.add(card)
        db.session.commit()
        return card

    def toggle_learned_status(self, card_id: int, user_id: int) -> bool:
        card = Flashcard.query.filter_by(id=card_id, user_id=user_id).first()
        if not card:
            raise ValueError("Flashcard not found")
        card.is_learned = not card.is_learned
        db.session.commit()
        return card.is_learned

    def delete_card(self, card_id: int, user_id: int) -> bool:
        card = Flashcard.query.filter_by(id=card_id, user_id=user_id).first()
        if not card:
            raise ValueError("Flashcard not found")
        db.session.delete(card)
        db.session.commit()
        return True
