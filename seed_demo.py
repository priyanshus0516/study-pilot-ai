"""
StudyPilot AI - Demo Database Seeder
Populates a turnkey demonstration environment with a demo student account,
pre-indexed course notes, question history, quiz attempts, flashcards, and weak-topic analytics.
"""
import os
import shutil
from datetime import datetime
from app import create_app
from database.database import db
from database.models import User, Document, DocumentChunk, QuestionHistory, Quiz, QuizQuestion, Flashcard, StudyActivity
from services.document_processor import DocumentProcessor

def seed_demo_data():
    app = create_app()
    with app.app_context():
        # Clean existing or recreate
        db.create_all()

        existing = User.query.filter_by(email="demo@studypilot.ai").first()
        if existing:
            print("Demo user already exists. Cleaning existing demo data for clean reload...")
            db.session.delete(existing)
            db.session.commit()

        # 1. Create Student User
        student = User(name="Priyanshu Sharma", email="demo@studypilot.ai")
        student.set_password("pilot123")
        db.session.add(student)
        db.session.commit()
        print(f"Created student user: {student.email} (Password: pilot123)")

        # 2. Index Sample Study Notes
        base_dir = os.path.abspath(os.path.dirname(__file__))
        sample_folder = os.path.join(base_dir, "sample_materials")
        user_upload_dir = os.path.join(base_dir, "uploads", f"user_{student.id}")
        os.makedirs(user_upload_dir, exist_ok=True)

        sample_files = [
            "OOP_Unit_4_Polymorphism.txt",
            "Computer_Networks_Protocols.txt"
        ]

        indexed_docs = []
        for s_file in sample_files:
            src_path = os.path.join(sample_folder, s_file)
            if not os.path.exists(src_path):
                continue

            dest_path = os.path.join(user_upload_dir, s_file)
            shutil.copyfile(src_path, dest_path)
            file_size = os.path.getsize(dest_path)

            chunks_data, total_pages = DocumentProcessor.process_file(dest_path, s_file)
            doc = Document(
                user_id=student.id,
                filename=s_file,
                file_path=dest_path,
                file_size=file_size,
                file_type="txt",
                total_pages=total_pages
            )
            db.session.add(doc)
            db.session.flush()

            for c in chunks_data:
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_text=c['chunk_text'],
                    page_number=c['page_number'],
                    chunk_index=c['chunk_index']
                )
                db.session.add(chunk)

            indexed_docs.append(doc)
            print(f"Indexed document: {s_file} with {len(chunks_data)} chunks.")

        # 3. Add Realistic Question & Answer History
        qa1 = QuestionHistory(
            user_id=student.id,
            document_id=indexed_docs[0].id if indexed_docs else None,
            question="What is a virtual function in C++ and why is it used?",
            answer=(
                "A virtual function is a member function declared within a base class using the keyword 'virtual' "
                "and overridden in a derived class. When accessed via a base class pointer or reference, C++ uses dynamic "
                "binding (via the internal VTABLE and VPTR mechanism) to execute the derived class's implementation. "
                "It enables runtime polymorphism, allowing different derived behaviors to be invoked through a uniform interface."
            ),
            source_reference="OOP_Unit_4_Polymorphism.txt – Page 1"
        )
        qa2 = QuestionHistory(
            user_id=student.id,
            document_id=indexed_docs[1].id if len(indexed_docs) > 1 else None,
            question="What is the difference between TCP and UDP?",
            answer=(
                "Transmission Control Protocol (TCP) is connection-oriented, guarantees delivery through acknowledgments and sequence numbers, "
                "and implements flow and congestion control. In contrast, User Datagram Protocol (UDP) is connectionless, lightweight, "
                "and unreliable (best-effort delivery without retransmission), making it ideal for streaming media and online gaming."
            ),
            source_reference="Computer_Networks_Protocols.txt – Page 1"
        )
        db.session.add_all([qa1, qa2])

        # 4. Add Quizzes with Topic Analytics (OOP: 90% High Mastery, Networks: 58% Weak Topic)
        # Quiz 1: OOP (Score: 9/10 = 90%)
        quiz_oop = Quiz(
            user_id=student.id,
            topic="Object Oriented Programming",
            difficulty="Medium",
            score=9,
            total_questions=10,
            completed=True
        )
        db.session.add(quiz_oop)
        db.session.flush()

        # Quiz 2: Computer Networks (Score: 5/10 = 50% -> triggers Weak Topic alert)
        quiz_net = Quiz(
            user_id=student.id,
            topic="Computer Networks",
            difficulty="Hard",
            score=5,
            total_questions=10,
            completed=True
        )
        db.session.add(quiz_net)
        db.session.flush()

        # Add questions for Networks Quiz
        net_questions = [
            ("Which layer of the OSI model handles end-to-end segmentation and flow control?", "Transport Layer", "Network Layer", "Data Link Layer", "Session Layer", "A", "Transport Layer (Layer 4) governs end-to-end transport."),
            ("What is the standard port number for DNS queries?", "53", "80", "443", "22", "A", "Domain Name System (DNS) operates on port 53."),
            ("Which protocol performs three-way handshake for establishing connections?", "TCP", "UDP", "ICMP", "ARP", "A", "TCP establishes connections via SYN, SYN-ACK, ACK handshake."),
            ("Which device operates primarily at Layer 3 (Network Layer) to route packets?", "Router", "Hub", "Repeater", "Bridge", "A", "Routers inspect Layer 3 IP headers to route packets."),
            ("What is the length of an IPv4 address in bits?", "32 bits", "64 bits", "128 bits", "16 bits", "A", "IPv4 addresses consist of 32 bits arranged into 4 octets.")
        ]
        for q_tuple in net_questions:
            qq = QuizQuestion(
                quiz_id=quiz_net.id,
                question=q_tuple[0],
                option_a=q_tuple[1],
                option_b=q_tuple[2],
                option_c=q_tuple[3],
                option_d=q_tuple[4],
                correct_answer=q_tuple[5],
                selected_answer="B" if q_tuple[0].startswith("Which device") else "A",
                explanation=q_tuple[6]
            )
            db.session.add(qq)

        # 5. Add Interactive Flashcards
        cards = [
            Flashcard(
                user_id=student.id,
                topic="Object Oriented Programming",
                question="What is dynamic dispatch in OOP?",
                answer="The process of selecting which polymorphic method implementation to call at runtime rather than compile-time.",
                is_learned=True
            ),
            Flashcard(
                user_id=student.id,
                topic="Object Oriented Programming",
                question="What is a pure virtual function?",
                answer="A virtual function equated to 0 (virtual void func() = 0;) that has no base implementation and makes the class abstract.",
                is_learned=True
            ),
            Flashcard(
                user_id=student.id,
                topic="Computer Networks",
                question="What is the primary role of the Transport Layer?",
                answer="Providing reliable end-to-end communication, packet sequencing, flow control, and error recovery across hosts.",
                is_learned=False
            ),
            Flashcard(
                user_id=student.id,
                topic="Computer Networks",
                question="Explain the TCP 3-Way Handshake.",
                answer="Client sends SYN -> Server responds with SYN-ACK -> Client acknowledges with ACK, establishing an open socket session.",
                is_learned=False
            )
        ]
        db.session.add_all(cards)

        # 6. Add Study Activity Records
        activities = [
            StudyActivity(user_id=student.id, activity_type="upload", duration=5, details="Uploaded OOP_Unit_4_Polymorphism.txt"),
            StudyActivity(user_id=student.id, activity_type="upload", duration=5, details="Uploaded Computer_Networks_Protocols.txt"),
            StudyActivity(user_id=student.id, activity_type="quiz_completed", duration=15, details="Completed Object Oriented Programming quiz (9/10)"),
            StudyActivity(user_id=student.id, activity_type="quiz_completed", duration=15, details="Completed Computer Networks quiz (5/10)"),
            StudyActivity(user_id=student.id, activity_type="qa", duration=10, details="Asked about virtual functions and VTABLE mechanisms"),
            StudyActivity(user_id=student.id, activity_type="flashcards_created", duration=8, details="Generated 4 active recall flashcards")
        ]
        db.session.add_all(activities)

        db.session.commit()
        print("Demo database successfully seeded!")
        print("Login credentials: demo@studypilot.ai / pilot123")

if __name__ == "__main__":
    seed_demo_data()
