/* ==========================================================================
   StudyPilot AI - Interactive Frontend Controller
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initFlashAlerts();
    initDropzones();
    initAIChat();
    initSummaries();
    initFlashcardCarousel();
});

// Flash Alerts auto-dismiss
function initFlashAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
}

// Drag & Drop Upload
function initDropzones() {
    const dropzone = document.getElementById('document-dropzone');
    const fileInput = document.getElementById('file-upload-input');
    const fileNameDisplay = document.getElementById('selected-file-name');

    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileName(files[0].name);
        }
    });

    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            updateFileName(fileInput.files[0].name);
        }
    });

    function updateFileName(name) {
        if (fileNameDisplay) {
            fileNameDisplay.textContent = `Selected: ${name}`;
            fileNameDisplay.style.display = 'block';
        }
    }
}

// Interactive Grounded AI Chat
function initAIChat() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const docSelect = document.getElementById('chat-doc-select');
    const messagesBox = document.getElementById('chat-messages');

    if (!chatForm || !chatInput || !messagesBox) return;

    // Fast prompt chips
    document.querySelectorAll('.prompt-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chatInput.value = chip.dataset.prompt || chip.textContent.trim();
            chatInput.focus();
        });
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;

        const docId = docSelect ? docSelect.value : null;

        // Append user message
        appendChatMessage('user', question);
        chatInput.value = '';
        scrollToBottom();

        // Append typing loader
        const loaderId = appendTypingLoader();
        scrollToBottom();

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    document_id: docId || null
                })
            });

            const data = await resp.json();
            removeTypingLoader(loaderId);

            if (resp.ok) {
                appendChatMessage('ai', data.answer, data.source, data.chunks);
            } else {
                appendChatMessage('ai', `⚠️ ${data.error || 'Could not fetch response from study material.'}`);
            }
        } catch (err) {
            removeTypingLoader(loaderId);
            appendChatMessage('ai', '⚠️ Network error communicating with StudyPilot server.');
        }

        scrollToBottom();
    });

    function appendChatMessage(sender, text, source = null, chunks = []) {
        const row = document.createElement('div');
        row.className = `message-row ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = `msg-avatar ${sender === 'user' ? 'user-av' : 'ai-av'}`;
        avatar.innerHTML = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-brain"></i>';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Format markdown bold and newlines
        let formatted = escapeHTML(text)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');

        bubble.innerHTML = formatted;

        if (source && source !== "None") {
            const srcDiv = document.createElement('div');
            srcDiv.innerHTML = `<span class="source-badge"><i class="fa-solid fa-book-open"></i> Source: ${escapeHTML(source)}</span>`;
            bubble.appendChild(srcDiv);
        }

        row.appendChild(avatar);
        row.appendChild(bubble);
        messagesBox.appendChild(row);
    }

    function appendTypingLoader() {
        const id = 'loader-' + Date.now();
        const row = document.createElement('div');
        row.id = id;
        row.className = 'message-row ai';
        row.innerHTML = `
            <div class="msg-avatar ai-av"><i class="fa-solid fa-brain"></i></div>
            <div class="message-bubble" style="color: var(--text-muted); font-style: italic;">
                <i class="fa-solid fa-circle-notch fa-spin"></i> Searching study notes and synthesizing answer...
            </div>
        `;
        messagesBox.appendChild(row);
        return id;
    }

    function removeTypingLoader(id) {
        const elem = document.getElementById(id);
        if (elem) elem.remove();
    }

    function scrollToBottom() {
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
}

// Summary Generator UI
function initSummaries() {
    const summaryBtn = document.getElementById('generate-summary-btn');
    const docSelect = document.getElementById('summary-doc-select');
    const resultBox = document.getElementById('summary-results-container');
    const loader = document.getElementById('summary-loader');

    if (!summaryBtn || !docSelect || !resultBox) return;

    let activeMode = 'medium';
    document.querySelectorAll('.summary-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.summary-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeMode = tab.dataset.mode;
        });
    });

    summaryBtn.addEventListener('click', async () => {
        const docId = docSelect.value;
        if (!docId) {
            alert('Please select a document first!');
            return;
        }

        resultBox.style.display = 'none';
        if (loader) loader.style.display = 'block';
        summaryBtn.disabled = true;

        try {
            const resp = await fetch('/summary/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    document_id: docId,
                    mode: activeMode
                })
            });
            const data = await resp.json();
            if (loader) loader.style.display = 'none';
            summaryBtn.disabled = false;

            if (resp.ok) {
                renderSummary(data);
            } else {
                alert(data.error || 'Failed to generate summary.');
            }
        } catch (e) {
            if (loader) loader.style.display = 'none';
            summaryBtn.disabled = false;
            alert('Error connecting to server.');
        }
    });

    function renderSummary(data) {
        resultBox.style.display = 'block';
        document.getElementById('summary-doc-title').textContent = data.document_name || 'Document Summary';
        document.getElementById('summary-mode-badge').textContent = (data.mode || 'medium').toUpperCase();
        document.getElementById('summary-body-text').textContent = data.summary;

        // Key Concepts
        const conceptsList = document.getElementById('summary-key-concepts');
        conceptsList.innerHTML = '';
        (data.key_concepts || []).forEach(c => {
            const li = document.createElement('li');
            li.textContent = c;
            conceptsList.appendChild(li);
        });

        // Definitions
        const defsList = document.getElementById('summary-definitions');
        defsList.innerHTML = '';
        (data.definitions || []).forEach(d => {
            const li = document.createElement('li');
            li.textContent = d;
            defsList.appendChild(li);
        });

        // Exam Points
        const examList = document.getElementById('summary-exam-points');
        examList.innerHTML = '';
        (data.exam_points || []).forEach(p => {
            const li = document.createElement('li');
            li.textContent = p;
            examList.appendChild(li);
        });

        resultBox.scrollIntoView({ behavior: 'smooth' });
    }
}

// 3D Flashcard Carousel
function initFlashcardCarousel() {
    const cardElement = document.getElementById('active-flashcard-3d');
    const prevBtn = document.getElementById('card-prev-btn');
    const nextBtn = document.getElementById('card-next-btn');
    const flipBtn = document.getElementById('card-flip-btn');
    const learnedBtn = document.getElementById('card-toggle-learned-btn');
    const counterDisplay = document.getElementById('card-counter');
    const frontText = document.getElementById('card-front-text');
    const backText = document.getElementById('card-back-text');
    const topicDisplay = document.getElementById('card-topic-display');

    if (!cardElement || !window.studyCards || window.studyCards.length === 0) return;

    let currentIndex = 0;
    const cards = window.studyCards;

    function renderCard(idx) {
        const c = cards[idx];
        cardElement.classList.remove('flipped');
        if (frontText) frontText.textContent = c.question;
        if (backText) backText.textContent = c.answer;
        if (topicDisplay) topicDisplay.textContent = c.topic || 'General';
        if (counterDisplay) counterDisplay.textContent = `Card ${idx + 1} of ${cards.length}`;

        if (learnedBtn) {
            learnedBtn.innerHTML = c.is_learned
                ? '<i class="fa-solid fa-check-circle" style="color: var(--success)"></i> Learned'
                : '<i class="fa-regular fa-circle"></i> Mark as Learned';
        }
    }

    cardElement.addEventListener('click', () => {
        cardElement.classList.toggle('flipped');
    });

    if (flipBtn) {
        flipBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            cardElement.classList.toggle('flipped');
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % cards.length;
            renderCard(currentIndex);
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + cards.length) % cards.length;
            renderCard(currentIndex);
        });
    }

    if (learnedBtn) {
        learnedBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const currentCard = cards[currentIndex];
            try {
                const resp = await fetch(`/flashcards/${currentCard.id}/toggle`, { method: 'POST' });
                const res = await resp.json();
                if (res.success) {
                    currentCard.is_learned = res.is_learned;
                    renderCard(currentIndex);
                }
            } catch (err) {
                console.error('Toggle failed', err);
            }
        });
    }

    renderCard(0);
}
