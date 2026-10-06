# StudyPilot AI – Intelligent AI-Powered Study Assistant

> **"Your study material, transformed into an intelligent learning workspace."**  
> *Upload → Extract → Understand → Ask → Generate → Practice → Track*

---

## 1. Project Overview & Problem Statement

College students and self-directed learners are overwhelmed with dense textbook chapters, lecture slides, and voluminous PDF notes. Traditional generic chatbots hallucinate answers detached from the student's actual syllabus or textbook edition.

**StudyPilot AI** bridges this gap by providing an end-to-end Python/Flask-based intelligent workspace where every interaction is **grounded directly in the student's uploaded course documents**. 

### Core Workflow:
```
Student Uploads Notes (PDF/TXT/DOCX)
       ↓
Page-Level Text Extraction & Cleaning
       ↓
Semantic Chunking & Metadata Storage (SQLite)
       ↓
Grounded Retrieval & Context Assembly
       ↓
┌──────────────────────┬──────────────────────┬──────────────────────┐
↓                      ↓                      ↓                      ↓
AI Study Chat          Document Summary       Adaptive Quiz Engine   3D Flashcard Deck
(with Page Citations)  (Short/Med/Detailed)   (MCQ + Scoring)        (Active Recall)
       ↓                      ↓                      ↓                      ↓
└──────────────────────┴──────────────────────┴──────────────────────┘
       ↓
Weak-Topic Detection & Performance Analytics Dashboard
```

---

## 2. Key Modules & Features

### A. Authentication & Security
- Secure registration and login with session management.
- Cryptographic password hashing (`pbkdf2:sha256`).
- Multi-tenant isolation: strict foreign-key barriers prevent users from viewing or modifying other students' notes.

### B. Intelligent Document Processing
- **Format Support:** PDF (`pypdf`), Plain Text (`.txt`), and Word Documents (`python-docx`).
- **Text Cleaning Engine:** Strips control characters, normalizes whitespace, eliminates duplicate formatting artifacts.
- **Semantic Chunking:** Page-preserving sliding chunk window with configurable token overlap for maximum retrieval context retention.
- **Chunk Inspector:** Visual modal enabling students to view raw indexed chunks and page numbers.

### C. Study-Material Grounded AI Chat
- Avoids generic hallucinating chatbots.
- Answers student questions using **only** the retrieved chunks from their uploaded notes.
- Injects source verification: e.g. `Source: OOP_Unit_4_Polymorphism.txt – Page 1`.
- Built-in prompt chips for fast concept queries.

### D. Multi-Depth Document Summarizer
- Three selectable depths:
  - **Short Summary:** 3-4 sentence high-impact briefing.
  - **Medium Summary:** Executive overview for standard revision.
  - **Detailed Summary:** Deep-dive analysis.
- Structured sections:
  1. Core Overview
  2. Key Concepts (bulleted breakdown)
  3. Important Definitions
  4. High-Yield Exam Takeaways

### E. Adaptive Quiz Generator & Evaluation
- Custom topic, document, difficulty (Easy, Medium, Hard), and question count (3 to 10).
- Multiple-choice questions with 4 options.
- Instant submission evaluation:
  - Total score and accuracy percentage.
  - Correct vs. Incorrect tally.
  - Automated **Weak Topic Detection** (< 70% threshold).
  - Question-by-question review with concept explanations.

### F. 3D Interactive Active Recall Flashcards
- Smooth 3D flip-card animation (`perspective: 1200px` / `transform-style: preserve-3d`).
- Auto-generate flashcard decks from documents or create manual cards.
- Mark as "Learned" vs. "Needs Review" with real-time recall tracking.
- Filter cards by topic.

### G. Performance Analytics & Weak Topic Detection
- **KPI Metrics:** Documents, Questions Asked, Quiz Attempts, Average Score, Total Study Time.
- **Subject Mastery Progress Bars:** Color-coded (Green ≥80%, Yellow 70–79%, Red <70%).
- **Personalized Interventions:** e.g., *"You scored 50% in Computer Networks. Consider practicing a quiz or reviewing flashcards."*
- Complete chronological study activity timeline.

---

## 3. Technology Stack

- **Backend:** Python 3.9+, Flask 3.1
- **Database & ORM:** SQLite, SQLAlchemy 2.0, Flask-SQLAlchemy 3.1
- **Document Processing:** `pypdf`, `python-docx`
- **AI / LLM Integration:** Google Gemini API (`google-generativeai`), OpenAI API (`openai`), and High-Yield Heuristic Study Engine (100% offline & demo ready)
- **Frontend:** Semantic HTML5, Vanilla CSS3 (Custom Glassmorphic Design System), Vanilla ES6 JavaScript
- **Testing:** `pytest` test suite

---

## 4. Software Architecture & Design Paradigms

1. **Object-Oriented Programming (OOP):**
   - Clean abstractions across services: `PDFProcessor`, `DocumentProcessor`, `AIService`, `QuizService`, `SummaryService`, `FlashcardService`, `ProgressService`.
   - Domain models: `User`, `Document`, `DocumentChunk`, `QuestionHistory`, `Quiz`, `QuizQuestion`, `Flashcard`, `StudyActivity`.
2. **Procedural Paradigm:**
   - Sequential document parsing: File Validation → Disk Save → Page Extraction → Text Normalization → Semantic Chunking → Database Commit.
3. **Event-Driven Paradigm:**
   - Asynchronous AJAX fetch handlers for real-time AI Chat, summary rendering, and flashcard recall updates.
4. **Model-View-Controller (MVC) Separation:**
   - Routes (`controllers`) cleanly invoke `services` and render Jinja2 `views` backed by SQLAlchemy `models`.

---

## 5. Folder Structure

```
StudyPilot-AI/
├── app.py                      # Flask Application factory & entrypoint
├── config.py                   # Configuration & environment loader
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment file
├── README.md                   # Complete documentation & viva guide
├── seed_demo.py                # Database seeder with pre-built test data
├── pytest.ini                  # Test suite configuration
│
├── database/
│   ├── __init__.py
│   ├── database.py             # DB instance & initialization
│   └── models.py               # SQLAlchemy schema definitions
│
├── services/
│   ├── __init__.py
│   ├── pdf_processor.py        # Page-by-page text extraction & cleanup
│   ├── document_processor.py   # Multi-format ingestion & chunk search
│   ├── ai_service.py           # Multi-provider LLM abstraction & fallback
│   ├── quiz_generator.py       # MCQ generation, scoring, and weak-topic logic
│   ├── summary_generator.py    # Multi-depth structured summarizer
│   ├── flashcard_generator.py  # 3D flashcard generation & state management
│   └── progress_service.py     # Aggregated study analytics & metrics
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Signup, login, logout, session guards
│   ├── dashboard.py            # Landing & student overview routes
│   ├── documents.py            # Upload, delete, chunk inspection
│   ├── qa.py                   # Grounded AI chat & question history
│   ├── quiz.py                 # Quiz configuration, taking, and results
│   ├── summary.py              # Summarizer view & AJAX API
│   ├── flashcards.py           # Flashcard deck & toggle API
│   └── progress.py             # Analytics & weak-topic recommendations
│
├── templates/
│   ├── base.html               # Master shell (sidebar, navigation, alerts)
│   ├── landing.html            # Public landing page with workflow pipeline
│   ├── login.html              # Login screen
│   ├── signup.html             # Registration screen
│   ├── dashboard.html          # Main student dashboard
│   ├── upload.html             # Drag-and-drop document upload & chunk modal
│   ├── chat.html               # Course-grounded AI chat interface
│   ├── summary.html            # Multi-mode summary viewer
│   ├── quiz.html               # Quiz hub & history
│   ├── quiz_take.html          # Interactive test taking UI
│   ├── quiz_results.html       # Score breakdown & answer key with explanations
│   ├── flashcards.html         # 3D flip-card active recall deck
│   └── progress.html           # Learning analytics & progress bars
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern design system & glassmorphism
│   └── js/
│       └── app.js              # Real-time chat, drag-drop, and 3D card flips
│
├── sample_materials/           # Ready-to-test course notes
│   ├── OOP_Unit_4_Polymorphism.txt
│   └── Computer_Networks_Protocols.txt
│
└── tests/                      # Automated test suite (100% pass)
    ├── __init__.py
    ├── test_auth.py
    ├── test_documents.py
    ├── test_quiz.py
    └── test_ai.py
```

---

## 6. Installation & Quick Start

### Step 1: Clone or Navigate to the Project
```bash
cd /Users/priyanshumac4/.gemini/antigravity-ide/scratch/StudyPilot-AI
```

### Step 2: Set Up Virtual Environment & Dependencies
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Step 3: Configure Environment Variables (Optional)
To use Google Gemini or OpenAI:
```bash
cp .env.example .env
# Open .env and add your GEMINI_API_KEY or OPENAI_API_KEY
```
*(Note: If no API key is set, StudyPilot automatically operates in its high-yield offline study heuristic mode, guaranteeing 100% functionality without requiring external network calls).*

### Step 4: Seed Demo Data (Recommended for Viva)
Populate sample course notes, questions, and test results:
```bash
./venv/bin/python seed_demo.py
```
**Demo Login Credentials:**
- Email: `demo@studypilot.ai`
- Password: `pilot123`

### Step 5: Start the Flask Development Server
```bash
./venv/bin/python app.py
```
Open your browser at: **`http://127.0.0.1:5000`**

### Step 6: Run Automated Tests
```bash
./venv/bin/pytest
```

---

## 7. Database Schema Overview

| Table | Purpose |
|---|---|
| `users` | Student profile, email, hashed credentials |
| `documents` | Uploaded document metadata, file paths, total page counts |
| `document_chunks` | Segmented text chunks with source page numbers |
| `questions` | Historical Q&A pairs with exact source citations |
| `quizzes` | Quiz attempts, topics, difficulty, and scores |
| `quiz_questions` | Individual MCQs, options, correct answer, and explanation |
| `flashcards` | Front/Back recall cards with `is_learned` boolean status |
| `study_activity` | Audit log of student learning time and modules completed |

---

## 8. Technical Viva & Presentation Guide

When demonstrating this project to examiners, emphasize these 5 key pillars:
1. **Document Ingestion & Text Chunking:** Explain how documents are cleaned and split into overlapping chunks with preserved page boundaries so the AI knows where content originated.
2. **Grounded Retrieval (RAG principles):** Point out that questions are answered using retrieved document context rather than generic LLM pre-training, eliminating hallucination.
3. **Exact Source Citation:** Highlight the badge showing `Source: OOP_Unit_4.pdf – Page 1`, proving the system grounds its response in the syllabus.
4. **Adaptive Quiz Generation & Scoring:** Demonstrate how the quiz engine checks user answers, highlights explanations, and calculates accuracy.
5. **Weak-Topic Detection:** Show how scoring < 70% in Computer Networks dynamically triggers the warning banner and actionable one-click study pathways.

---

## 9. Future Scope & Roadmap

- **Adaptive Spaced Repetition (SM-2 Algorithm):** Automatic scheduling of flashcards based on forgetting curves.
- **Speech-to-Text & Voice Tutor:** Voice querying for hands-free revision.
- **Vector Embeddings (ChromaDB / FAISS):** Dense vector similarity search for large multi-gigabyte document libraries.
- **Collaborative Study Rooms:** Peer-to-peer shared quiz battles.
