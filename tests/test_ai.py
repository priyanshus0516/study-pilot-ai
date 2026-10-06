import pytest
from services.document_processor import DocumentProcessor
from services.ai_service import AIService

def test_grounded_chunk_search():
    """Verify semantic keyword ranking retrieves the most relevant chunk."""
    chunks = [
        {"page_number": 1, "chunk_text": "Introduction to computer networks: OSI model and TCP/IP stack layers."},
        {"page_number": 2, "chunk_text": "Virtual functions in C++ allow runtime polymorphism and dynamic dispatch using vtables."},
        {"page_number": 3, "chunk_text": "Relational databases use SQL, normal forms, and ACID transactions for consistency."}
    ]

    # Query about virtual functions
    matches = DocumentProcessor.search_relevant_chunks(chunks, "What is a virtual function?", top_k=1)
    assert len(matches) == 1
    assert matches[0]["page_number"] == 2
    assert "runtime polymorphism" in matches[0]["chunk_text"]

def test_grounded_qa_response_generation():
    """Verify answer is synthesized with exact page reference."""
    chunks = [
        {"page_number": 12, "chunk_text": "A virtual function is a member function in base class that is redefined in derived class."}
    ]

    ai_service = AIService()
    result = ai_service.answer_question(
        question="What is a virtual function?",
        chunks=chunks,
        doc_name="OOP_Unit_4.pdf"
    )

    assert "answer" in result
    assert "source" in result
    assert "OOP_Unit_4.pdf – Page 12" in result["source"]
    assert "virtual function" in result["answer"].lower()

def test_summary_generation_structure():
    """Verify summary output contains key concepts, definitions, and exam points."""
    text = (
        "Object-Oriented Programming (OOP) is a programming paradigm based on the concept of objects. "
        "Encapsulation is defined as the bundling of data with methods that operate on that data. "
        "Inheritance allows a new class to inherit attributes from a base class. "
        "Polymorphism refers to the ability of different classes to respond to the same message."
    )

    ai_service = AIService()
    res = ai_service.generate_summary(text, mode="medium")

    assert "summary" in res
    assert "key_concepts" in res
    assert "definitions" in res
    assert "exam_points" in res
    assert len(res["exam_points"]) > 0
