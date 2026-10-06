import os
import re
import json
from typing import List, Dict, Any, Optional
from config import Config

class AIService:
    """
    Central AI orchestration service supporting Google Gemini,
    OpenAI (ChatGPT), and a robust grounded study-NLP heuristic fallback.
    """

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        Config.reload_env()
        self.gemini_key = Config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.openai_key = Config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.provider_pref = (Config.DEFAULT_AI_PROVIDER or "auto").lower()
        raw_gemini_model = Config.GEMINI_MODEL or "gemini-3.8-flash"
        # Ensure model name uses the 'models/' prefix required by new Google AI SDK
        self.gemini_model_name = raw_gemini_model if raw_gemini_model.startswith("models/") else f"models/{raw_gemini_model}"
        self.openai_model_name = Config.OPENAI_MODEL or "gpt-4o-mini"
        self._setup_client()

    def _setup_client(self):
        self.active_provider = "offline"
        self.active_model = "heuristic-study-engine"
        
        # Priority 1: Gemini if explicitly requested or auto with key
        if self.provider_pref in ["auto", "gemini"] and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
                self.active_provider = "gemini"
                self.active_model = self.gemini_model_name
                return
            except Exception as e:
                print(f"Gemini init warning: {e}")

        # Priority 2: OpenAI (ChatGPT) if explicitly requested or auto with key
        if self.provider_pref in ["auto", "openai"] and self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.active_provider = "openai"
                self.active_model = self.openai_model_name
                return
            except Exception as e:
                print(f"OpenAI init warning: {e}")

        # Default: smart grounded study NLP engine
        self.active_provider = "offline"
        self.active_model = "StudyPilot Heuristic Engine"

    def get_status_info(self) -> Dict[str, str]:
        if self.active_provider == "gemini":
            return {
                "provider": "gemini",
                "name": f"Google Gemini ({self.active_model})",
                "badge_class": "badge-gemini",
                "icon": "fa-google",
                "is_live": True
            }
        elif self.active_provider == "openai":
            return {
                "provider": "openai",
                "name": f"ChatGPT ({self.active_model})",
                "badge_class": "badge-openai",
                "icon": "fa-robot",
                "is_live": True
            }
        else:
            return {
                "provider": "offline",
                "name": "Local Heuristic Engine (Offline)",
                "badge_class": "badge-offline",
                "icon": "fa-bolt",
                "is_live": False
            }

    @staticmethod
    def test_connection(provider: str, api_key: str, model_name: str = "") -> Dict[str, Any]:
        """
        Tests live API connection for either Google Gemini or OpenAI ChatGPT.
        """
        if not api_key:
            return {"success": False, "message": "API key cannot be empty."}

        provider = provider.lower()
        if provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                # Normalize model name to use 'models/' prefix
                resolved_model = model_name or "gemini-3.8-flash"
                if not resolved_model.startswith("models/"):
                    resolved_model = f"models/{resolved_model}"
                m = genai.GenerativeModel(resolved_model)
                response = m.generate_content("Respond with exactly one word: 'READY'")
                if response and response.text:
                    return {
                        "success": True,
                        "message": f"Connected to Google Gemini ({resolved_model}) successfully!"
                    }
                return {"success": False, "message": "No response text received from Gemini."}
            except Exception as e:
                return {"success": False, "message": f"Gemini Error: {str(e)}"}

        elif provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model=model_name or "gpt-4o-mini",
                    messages=[{"role": "user", "content": "Respond with 'READY'"}],
                    max_tokens=10
                )
                if resp and resp.choices:
                    return {
                        "success": True,
                        "message": f"Connected to OpenAI ChatGPT ({model_name or 'gpt-4o-mini'}) successfully!"
                    }
                return {"success": False, "message": "No response choice returned by OpenAI."}
            except Exception as e:
                return {"success": False, "message": f"OpenAI Error: {str(e)}"}

        return {"success": False, "message": f"Unknown provider: {provider}"}

    # ==========================================
    # 1. GROUNDED QUESTION ANSWERING
    # ==========================================
    def answer_question(self, question: str, chunks: List[Any], doc_name: str = "Document") -> Dict[str, Any]:
        """
        Answers a user question grounded strictly in retrieved chunks.
        """
        if not chunks:
            return {
                "answer": "No relevant content was found in your uploaded study material to answer this question. Please upload relevant notes or try rephrasing.",
                "source": "None"
            }

        # Build context with page references
        context_parts = []
        page_refs = []
        for ch in chunks:
            p_num = ch.page_number if hasattr(ch, 'page_number') else ch.get('page_number', 1)
            c_text = ch.chunk_text if hasattr(ch, 'chunk_text') else ch.get('chunk_text', '')
            context_parts.append(f"[Page {p_num}]: {c_text}")
            if p_num not in page_refs:
                page_refs.append(p_num)

        context_str = "\n\n".join(context_parts)
        page_str = ", ".join(f"Page {p}" for p in sorted(page_refs))
        source_ref = f"{doc_name} – {page_str}"

        prompt = (
            f"You are StudyPilot AI, an intelligent academic tutor.\n"
            f"Answer the following student question using ONLY the provided study material context.\n"
            f"Be precise, clear, and educational. Format with clean bullet points or steps where helpful.\n"
            f"If the answer is not mentioned in the context, clearly explain that it is not covered in the uploaded material.\n\n"
            f"STUDY CONTEXT:\n{context_str}\n\n"
            f"STUDENT QUESTION:\n{question}\n\n"
            f"ANSWER:"
        )

        # Try Gemini if active
        if self.active_provider == "gemini":
            try:
                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    return {
                        "answer": response.text.strip(),
                        "source": source_ref
                    }
            except Exception as e:
                print(f"Gemini API error in Q&A: {e}")

        # Try OpenAI if active
        elif self.active_provider == "openai":
            try:
                resp = self.openai_client.chat.completions.create(
                    model=self.active_model,
                    messages=[
                        {"role": "system", "content": "You are StudyPilot AI, an intelligent study assistant grounded strictly in student notes."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                return {
                    "answer": resp.choices[0].message.content.strip(),
                    "source": source_ref
                }
            except Exception as e:
                print(f"OpenAI API error in Q&A: {e}")

        # Grounded NLP extraction fallback
        return self._heuristic_qa(question, chunks, doc_name, page_str)

    def _heuristic_qa(self, question: str, chunks: List[Any], doc_name: str, page_str: str) -> Dict[str, Any]:
        """
        Synthesizes an informative answer from retrieved document chunks.
        """
        extracted_sentences = []
        q_tokens = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', question)]

        for ch in chunks:
            text = ch.chunk_text if hasattr(ch, 'chunk_text') else ch.get('chunk_text', '')
            sentences = re.split(r'(?<=[.!?]) +', text)
            for s in sentences:
                s_clean = s.strip()
                if not s_clean:
                    continue
                score = sum(1 for tok in q_tokens if tok in s_clean.lower())
                if score > 0 and len(s_clean) > 25:
                    extracted_sentences.append((score, s_clean))

        extracted_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in extracted_sentences[:4]]

        if not top_sentences:
            first_chunk_text = (chunks[0].chunk_text if hasattr(chunks[0], 'chunk_text') else chunks[0].get('chunk_text', ''))
            top_sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', first_chunk_text)[:3] if s.strip()]

        synthesized = " ".join(top_sentences)
        answer = (
            f"Based on your uploaded material (**{doc_name}**):\n\n"
            f"{synthesized}\n\n"
            f"*Key takeaway*: This concept is directly detailed in your uploaded study notes."
        )

        return {
            "answer": answer,
            "source": f"{doc_name} – {page_str}"
        }

    # ==========================================
    # 2. DOCUMENT SUMMARIZATION
    # ==========================================
    def generate_summary(self, full_text: str, mode: str = "medium") -> Dict[str, Any]:
        prompt = (
            f"You are StudyPilot AI. Analyze the following study material and generate a structured summary in JSON format with keys:\n"
            f"- 'summary': (A {mode} summary: short ~3-4 sentences, medium ~2 paragraphs, detailed ~4 paragraphs)\n"
            f"- 'key_concepts': list of 4-6 key concepts covered with 1-line explanations\n"
            f"- 'definitions': list of 3-5 critical term definitions\n"
            f"- 'exam_points': list of 4-6 high-yield exam takeaways\n\n"
            f"MATERIAL:\n{full_text[:4000]}\n\n"
            f"Return ONLY valid JSON."
        )

        if self.active_provider == "gemini":
            try:
                response = self.gemini_model.generate_content(prompt)
                parsed = self._extract_json(response.text)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"Gemini summary error: {e}")

        elif self.active_provider == "openai":
            try:
                resp = self.openai_client.chat.completions.create(
                    model=self.active_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                parsed = self._extract_json(resp.choices[0].message.content)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"OpenAI summary error: {e}")

        return self._heuristic_summary(full_text, mode)

    def _heuristic_summary(self, text: str, mode: str) -> Dict[str, Any]:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 30]

        if mode == "short":
            summary_text = " ".join(sentences[:3]) if sentences else text[:250]
        elif mode == "detailed":
            summary_text = "\n\n".join(paragraphs[:5]) if len(paragraphs) >= 3 else text[:1200]
        else:
            summary_text = "\n\n".join(paragraphs[:3]) if len(paragraphs) >= 2 else " ".join(sentences[:5])

        definitions = []
        for s in sentences:
            if re.search(r'\b(is a|is an|refers to|is defined as|means)\b', s, re.IGNORECASE):
                if len(s) < 200 and s not in definitions:
                    definitions.append(s)
            if len(definitions) >= 4:
                break
        if not definitions:
            definitions = [
                "Key concepts are structured systematically within this module.",
                "Foundational terminologies define the core mechanisms outlined in the notes."
            ]

        concepts = []
        concept_candidates = re.findall(r'\b[A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]+)?\b', text)
        freq = {}
        for c in concept_candidates:
            if c.lower() not in {'this', 'that', 'these', 'there', 'what', 'when', 'chapter', 'unit', 'page', 'table'}:
                freq[c] = freq.get(c, 0) + 1
        sorted_concepts = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        for term, _ in sorted_concepts[:5]:
            concepts.append(f"{term}: Core subject principle analyzed in this chapter.")

        if not concepts:
            concepts = [
                "Core Architecture & Foundations: Principles governing the uploaded subject matter.",
                "Procedural Implementation: Step-by-step logic and operational rules.",
                "Practical Applications: Real-world problem solving and exam methodology."
            ]

        exam_points = [
            "Be prepared to differentiate primary concepts and provide code/real-world examples.",
            "Understand the internal mechanisms, advantages, and limitations discussed in the text.",
            "Review syntax, keywords, and architectural diagrams highlighted in the notes.",
            "Pay close attention to runtime behaviors and foundational definitions for viva questions."
        ]

        return {
            "summary": summary_text,
            "key_concepts": concepts,
            "definitions": definitions,
            "exam_points": exam_points
        }

    # ==========================================
    # 3. QUIZ GENERATION
    # ==========================================
    def generate_quiz(self, text: str, topic: str, difficulty: str = "Medium", num_questions: int = 5) -> List[Dict[str, Any]]:
        prompt = (
            f"Generate {num_questions} multiple choice quiz questions about '{topic}' (Difficulty: {difficulty}) "
            f"based on the following study text.\n\n"
            f"TEXT:\n{text[:4000]}\n\n"
            f"Return a JSON array of objects with keys:\n"
            f"- 'question': string\n"
            f"- 'option_a': string\n"
            f"- 'option_b': string\n"
            f"- 'option_c': string\n"
            f"- 'option_d': string\n"
            f"- 'correct_answer': 'A' or 'B' or 'C' or 'D'\n"
            f"- 'explanation': string explaining why this is correct\n\n"
            f"Return ONLY valid JSON array."
        )

        if self.active_provider == "gemini":
            try:
                response = self.gemini_model.generate_content(prompt)
                parsed = self._extract_json(response.text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:num_questions]
            except Exception as e:
                print(f"Gemini quiz error: {e}")

        elif self.active_provider == "openai":
            try:
                resp = self.openai_client.chat.completions.create(
                    model=self.active_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4
                )
                parsed = self._extract_json(resp.choices[0].message.content)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:num_questions]
            except Exception as e:
                print(f"OpenAI quiz error: {e}")

        return self._heuristic_quiz(text, topic, difficulty, num_questions)

    def _heuristic_quiz(self, text: str, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 35]
        questions = []
        pattern = re.compile(r'^(.*?)\s+(is an?|refers to|means|is defined as|provides|enables)\s+(.*)$', re.IGNORECASE)
        
        for s in sentences:
            m = pattern.search(s)
            if m and len(questions) < count:
                subject = m.group(1).strip()
                predicate = m.group(3).strip()
                if 2 <= len(subject.split()) <= 6 and len(predicate) > 15:
                    q = {
                        "question": f"Which of the following best describes {subject}?",
                        "option_a": predicate[:100] if len(predicate) > 100 else predicate,
                        "option_b": f"It is exclusively used to disable {subject} operations.",
                        "option_c": f"A legacy compiler directive unrelated to {topic}.",
                        "option_d": "A physical hardware register used during cache flushing.",
                        "correct_answer": "A",
                        "explanation": f"According to your study material: {s}"
                    }
                    questions.append(q)

        default_templates = [
            (
                f"What is the primary role of {topic} in modern software engineering?",
                f"To structure logic and optimize modular reusability in {topic}.",
                "To increase redundant code complexity.",
                "To bypass operating system kernel protection.",
                "To eliminate memory usage completely.",
                "A",
                f"The core benefit of {topic} is achieving high modularity and clean architectural design."
            ),
            (
                f"When working with {topic}, which consideration is most critical for performance?",
                "Algorithmic efficiency and correct memory management.",
                "The color scheme of the source code editor.",
                "Using randomized variable names.",
                "Disabling all compile-time type validations.",
                "A",
                "Proper resource management and algorithmic structure dictate execution efficiency."
            ),
            (
                f"In the context of {topic}, what does procedural vs object-oriented design dictate?",
                "Procedural focuses on step-by-step routines while OOP encapsulates data and behaviors.",
                "Both are identical and compiled into scripts without difference.",
                "OOP is solely for web browsers while procedural is for mobile devices.",
                "Procedural programming cannot execute arithmetic calculations.",
                "A",
                "Procedural programming arranges code linearly, while OOP groups states into objects."
            ),
            (
                f"Which best practice should be followed when testing systems in {topic}?",
                "Validating boundary cases, input sanitization, and regression test suites.",
                "Skipping unit tests if the code compiles once.",
                "Assuming all external network calls succeed unconditionally.",
                "Removing all error handling to speed up runtime execution.",
                "A",
                "Robust software requires rigorous unit testing and defensive input validation."
            ),
            (
                f"What is the typical lifecycle order in {topic} execution?",
                "Initialization → Processing / Event handling → Resource Cleanup.",
                "Termination → Allocation → Compilation.",
                "Random execution without stack frames.",
                "Compilation only without runtime execution.",
                "A",
                "Standard execution flow moves from initialization to active loop and finally resource teardown."
            )
        ]

        idx = 0
        while len(questions) < count and idx < len(default_templates):
            t = default_templates[idx]
            questions.append({
                "question": t[0],
                "option_a": t[1],
                "option_b": t[2],
                "option_c": t[3],
                "option_d": t[4],
                "correct_answer": t[5],
                "explanation": t[6]
            })
            idx += 1

        return questions[:count]

    # ==========================================
    # 4. FLASHCARD GENERATION
    # ==========================================
    def generate_flashcards(self, text: str, topic: str, count: int = 6) -> List[Dict[str, Any]]:
        prompt = (
            f"Generate {count} educational flashcards for topic '{topic}' based on this study text:\n\n"
            f"{text[:3500]}\n\n"
            f"Return a JSON array of objects with keys:\n"
            f"- 'question': front of card (e.g., 'What is Polymorphism?')\n"
            f"- 'answer': back of card (concise, clear definition/explanation)\n"
            f"- 'topic': '{topic}'\n\n"
            f"Return ONLY valid JSON array."
        )

        if self.active_provider == "gemini":
            try:
                response = self.gemini_model.generate_content(prompt)
                parsed = self._extract_json(response.text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:count]
            except Exception as e:
                print(f"Gemini flashcards error: {e}")

        elif self.active_provider == "openai":
            try:
                resp = self.openai_client.chat.completions.create(
                    model=self.active_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                parsed = self._extract_json(resp.choices[0].message.content)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[:count]
            except Exception as e:
                print(f"OpenAI flashcards error: {e}")

        return self._heuristic_flashcards(text, topic, count)

    def _heuristic_flashcards(self, text: str, topic: str, count: int) -> List[Dict[str, Any]]:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 35]
        cards = []

        for s in sentences:
            m = re.match(r'^(.*?)\s+(is an?|refers to|means|is defined as)\s+(.*)$', s, re.IGNORECASE)
            if m and len(cards) < count:
                subj = m.group(1).strip()
                ans = m.group(3).strip()
                if 2 <= len(subj.split()) <= 6 and len(ans) > 15:
                    cards.append({
                        "question": f"What is {subj}?",
                        "answer": f"{subj.capitalize()} {m.group(2).lower()} {ans}",
                        "topic": topic
                    })

        defaults = [
            (f"What is the core principle of {topic}?", f"{topic} organizes complex systems into manageable, testable components."),
            (f"Why is {topic} critical in exams and interviews?", f"Questions test conceptual clarity, syntax understanding, and real-world system applications."),
            (f"What is the difference between static and dynamic behavior in {topic}?", "Static occurs at compile-time (e.g. overloading), while dynamic occurs at runtime (e.g. virtual functions/overriding)."),
            (f"How do you optimize performance when implementing {topic}?", "Minimize redundant memory allocations and leverage efficient algorithmic complexity."),
            (f"What are key pitfalls to avoid in {topic}?", "Neglecting edge conditions, unhandled exceptions, and poor separation of concerns."),
            (f"What is an example Viva question on {topic}?", f"'Explain the architectural lifecycle and practical use-cases of {topic} with code.'")
        ]

        idx = 0
        while len(cards) < count and idx < len(defaults):
            cards.append({
                "question": defaults[idx][0],
                "answer": defaults[idx][1],
                "topic": topic
            })
            idx += 1

        return cards[:count]

    @staticmethod
    def _extract_json(text: str) -> Optional[Any]:
        if not text:
            return None
        cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'```$', '', cleaned.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned.strip())
        except Exception:
            start_bracket = cleaned.find('[')
            start_brace = cleaned.find('{')
            if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
                end_bracket = cleaned.rfind(']')
                if end_bracket != -1:
                    try:
                        return json.loads(cleaned[start_bracket:end_bracket+1])
                    except Exception:
                        pass
            elif start_brace != -1:
                end_brace = cleaned.rfind('}')
                if end_brace != -1:
                    try:
                        return json.loads(cleaned[start_brace:end_brace+1])
                    except Exception:
                        pass
        return None
