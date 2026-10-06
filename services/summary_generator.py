from typing import Dict, Any, Optional
from database.database import db
from database.models import Document, StudyActivity
from services.ai_service import AIService

class SummaryService:
    def __init__(self):
        self.ai_service = AIService()

    def generate_document_summary(
        self,
        user_id: int,
        document_id: int,
        mode: str = "medium"
    ) -> Dict[str, Any]:
        """
        Retrieves document content, generates a structured summary with key concepts,
        definitions, and exam points, and logs study activity.
        """
        doc = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not doc:
            raise ValueError("Document not found")

        # Collect text from chunks
        full_text = "\n\n".join([chunk.chunk_text for chunk in doc.chunks])
        if not full_text.strip():
            full_text = f"Content extracted from {doc.filename}"

        summary_data = self.ai_service.generate_summary(full_text=full_text, mode=mode)
        
        # Add metadata
        summary_data['document_id'] = doc.id
        summary_data['document_name'] = doc.filename
        summary_data['mode'] = mode

        # Log activity
        activity = StudyActivity(
            user_id=user_id,
            activity_type='summary_generated',
            duration=8,
            details=f"Generated {mode} summary for {doc.filename}"
        )
        db.session.add(activity)
        db.session.commit()

        return summary_data
