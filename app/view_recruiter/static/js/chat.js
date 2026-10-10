/**
 * Renders the small Markdown subset the assistant uses (bold, inline code, lists,
 * headings and links) as HTML. The text is escaped first, so any HTML in a message
 * is shown as text, and only http(s) and mailto links become anchors.
 */
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function chatLink(url, label) {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
}

function renderChatInline(text) {
    // Finished anchors are parked behind placeholders so the raw-URL pass
    // does not link the href of a Markdown link a second time.
    const parked = [];
    const park = (html) => `\u0000${parked.push(html) - 1}\u0000`;

    let html = text.replace(/\[([^\]\n]+)\]\(((?:https?:\/\/|mailto:)[^)\s]+)\)/gi,
        (match, label, url) => park(chatLink(url, label)));
    html = html.replace(/https?:\/\/[^\s<\u0000]+/gi, (match) => {
        // Trailing punctuation and escaped quotes belong to the sentence, not the URL.
        const trailing = match.match(/(?:[.,;:!?)\]]|&quot;|&#39;)+$/);
        const url = trailing ? match.slice(0, -trailing[0].length) : match;
        return park(chatLink(url, url)) + (trailing ? trailing[0] : '');
    });
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    return html.replace(/\u0000(\d+)\u0000/g, (match, i) => parked[Number(i)]);
}

function renderChatMarkdown(text) {
    const lines = escapeHtml(String(text).replace(/\u0000/g, '')).split('\n');
    const blocks = [];
    let list = null;

    for (const line of lines) {
        const bullet = line.match(/^\s*[-*] +(.*)$/);
        const numbered = line.match(/^\s*\d+[.)] +(.*)$/);
        const item = bullet || numbered;
        if (item) {
            const tag = bullet ? 'ul' : 'ol';
            if (!list || list.tag !== tag) {
                list = { tag, items: [] };
                blocks.push(list);
            }
            list.items.push(renderChatInline(item[1]));
            continue;
        }
        list = null;
        const heading = line.match(/^#{1,6} +(.*)$/);
        blocks.push(heading ? `<strong>${renderChatInline(heading[1])}</strong>` : renderChatInline(line));
    }

    let html = '';
    blocks.forEach((block, i) => {
        if (typeof block === 'string') {
            const previous = blocks[i - 1];
            if (i > 0 && typeof previous === 'string') html += '<br>';
            html += block;
        } else {
            const items = block.items.map((item) => `<li>${item}</li>`).join('');
            html += `<${block.tag}>${items}</${block.tag}>`;
        }
    });
    return html;
}

window.initializeRecruiterView = function (callbacks) {
    const chatWindow = document.getElementById("chat-window");
    if (!chatWindow || chatWindow.dataset.viewInitialized) {
        return;
    }
    chatWindow.dataset.viewInitialized = "true";
    console.log("Initializing Recruiter (Chat) View Specifics...");

    const windowControls = initializeDraggableWindow({
        windowId: "chat-window",
        titleBarId: "chat-title-bar",
        closeBtnId: "chat-close",
        minimizeBtnId: "chat-minimize",
        maximizeBtnId: "chat-maximize",
        onClose: callbacks.onClose,
    });

    // Scoped querySelector to avoid race conditions with the main document
    const chatMessages = chatWindow.querySelector('#chat-messages');
    const chatForm = chatWindow.querySelector('#chat-form');
    const chatInput = chatWindow.querySelector('#chat-input');
    const sendButton = chatWindow.querySelector('#chat-send-button');

    const modal = chatWindow.querySelector('#chat-modal');
    const modalTitle = chatWindow.querySelector('#chat-modal-title');
    const modalText = chatWindow.querySelector('#chat-modal-text');
    const modalClose = chatWindow.querySelector('#chat-modal-close');

    if (!chatMessages || !chatForm || !chatInput || !sendButton || !modal) {
        console.error("One or more Chat UI content elements are missing!");
        return;
    }

    let isLoading = false;
    let chatState = 'awaiting_code';
    const TOKEN_KEY = 'app_access_token';
    const THEME_KEY = 'cli_theme';
    let conversationHistory = [];
    const maxChars = parseInt(chatWindow.dataset.maxChars, 10) || 0;

    function applyTheme(themeName) {
        chatWindow.dataset.theme = themeName;
    }

    function addMessage(text, sender) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);
        bubble.innerHTML = renderChatMarkdown(text);
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubble;
    }

    // Spinner frames: braille, which no system draws as emoji.
    const SPINNER_FRAMES = '\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f';
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let spinnerTimers = [];

    // Bot bubble with a spinner and a comment while the reply is on its way.
    // textKey holds the comments separated by "|": one is picked at random and
    // another one replaces it every few seconds.
    function showWorking(textKey) {
        hideWorking();
        const comments = uiText(textKey).split('|').map(c => c.trim()).filter(Boolean);
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', 'bot', 'working');
        bubble.id = 'working-indicator';
        bubble.setAttribute('role', 'status');
        const glyph = document.createElement('span');
        glyph.className = 'spinner-glyph';
        glyph.setAttribute('aria-hidden', 'true');
        const label = document.createElement('span');
        label.className = 'spinner-text';
        bubble.append(glyph, label);

        let frame = 0;
        let shown = -1;
        const nextFrame = () => {
            glyph.textContent = SPINNER_FRAMES[frame++ % SPINNER_FRAMES.length];
        };
        const nextComment = () => {
            let pick = Math.floor(Math.random() * comments.length);
            if (comments.length > 1 && pick === shown) pick = (pick + 1) % comments.length;
            shown = pick;
            label.textContent = comments[pick] || '';
        };
        nextFrame();
        nextComment();
        if (!reducedMotion) spinnerTimers.push(setInterval(nextFrame, 80));
        if (comments.length > 1) spinnerTimers.push(setInterval(nextComment, 2500));

        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function hideWorking() {
        spinnerTimers.forEach(clearInterval);
        spinnerTimers = [];
        chatWindow.querySelector('#working-indicator')?.remove();
    }

    function setInputState(enabled, placeholder) {
        chatInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        chatInput.placeholder = placeholder;
        if (enabled && modal.hidden) chatInput.focus();
    }

    // Notice over the chat for a refused message; it stays until dismissed.
    function showNotice(title, text) {
        modalTitle.textContent = title;
        modalText.textContent = text;
        modal.hidden = false;
        modalClose.focus();
    }

    function hideNotice() {
        if (modal.hidden) return;
        modal.hidden = true;
        if (!chatInput.disabled) chatInput.focus();
    }

    function handleModalClick(event) {
        if (event.target === modal) hideNotice();
    }

    function handleModalKey(event) {
        if (event.key === 'Escape') hideNotice();
    }

    function showTooLong(count, max) {
        showNotice(uiText('chat.too_long_title'),
            uiText('chat.too_long_text', { max, count }));
    }

    // Minutes to wait, from the seconds the server sends in retry_after.
    async function retryMinutes(response) {
        const data = await response.json().catch(() => ({}));
        return Math.max(1, Math.ceil((Number(data.retry_after) || 60) / 60));
    }

    async function handleCodeSubmission(code) {
        isLoading = true;
        setInputState(false, uiText('chat.verifying'));
        showWorking('chat.verifying');

        try {
            const response = await fetch('/auth/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code: code}),
            });

            hideWorking();

            if (response.status === 429) {
                const minutes = await retryMinutes(response);
                setInputState(true, uiText('chat.code_placeholder'));
                showNotice(uiText('chat.locked_title'),
                    uiText('chat.locked_text', { minutes }));
                return;
            }
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || uiText('chat.wrong_code'));
            }

            const data = await response.json();
            sessionStorage.setItem(TOKEN_KEY, data.token);
            chatState = 'chatting';
            chatInput.classList.remove('password-mask');
            const welcomeMsg = uiText('chat.access_granted');
            addMessage(welcomeMsg, 'bot');
            conversationHistory.push({role: 'assistant', content: welcomeMsg});
            setInputState(true, uiText('chat.ask_placeholder'));

        } catch (error) {
            addMessage(uiText('chat.wrong_code'), 'bot');
            setInputState(true, uiText('chat.code_placeholder'));
        } finally {
            isLoading = false;
        }
    }

    async function handleChatMessage(message) {
        isLoading = true;
        setInputState(false, uiText('chat.thinking'));
        const userBubble = addMessage(message, 'user');
        conversationHistory.push({role: 'user', content: message});
        showWorking('chat.working');

        const token = sessionStorage.getItem(TOKEN_KEY);
        if (!token) {
            hideWorking();
            addMessage(uiText('chat.session_expired'), 'bot');
            chatState = 'awaiting_code';
            chatInput.classList.add('password-mask');
            conversationHistory = [];
            setInputState(true, uiText('chat.code_placeholder'));
            isLoading = false;
            return;
        }

        try {
            const response = await fetch('/recruiter/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(0, -1)
                }),
            });

            hideWorking();

            if (response.status === 401) {
                sessionStorage.removeItem(TOKEN_KEY);
                addMessage(uiText('chat.session_expired'), 'bot');
                chatState = 'awaiting_code';
                chatInput.classList.add('password-mask');
                conversationHistory = [];
                setInputState(true, uiText('chat.code_placeholder'));
                return;
            }
            if (response.status === 413 || response.status === 429) {
                // Refused before reaching the model: the message goes back to
                // the input, to be shortened or sent later.
                userBubble.remove();
                conversationHistory.pop();
                chatInput.value = message;
                if (response.status === 413) {
                    const data = await response.json().catch(() => ({}));
                    showTooLong(message.length, data.max_chars || maxChars);
                } else {
                    const minutes = await retryMinutes(response);
                    showNotice(uiText('chat.rate_title'),
                        uiText('chat.rate_text', { minutes }));
                }
                return;
            }
            if (!response.ok) throw new Error(uiText('chat.unavailable'));

            const data = await response.json();
            addMessage(data.reply, 'bot');
            conversationHistory = data.history || [];

        } catch (error) {
            hideWorking();
            addMessage(uiText('chat.error', { error: error.message }), 'bot');
            conversationHistory.pop();
        } finally {
            isLoading = false;
            setInputState(true, uiText('chat.ask_another'));
        }
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        const userInput = chatInput.value.trim();
        if (!userInput || isLoading) return;
        if (chatState === 'chatting' && maxChars && userInput.length > maxChars) {
            // The text stays in the input, to be shortened.
            showTooLong(userInput.length, maxChars);
            return;
        }
        chatInput.value = '';

        if (chatState === 'awaiting_code') {
            handleCodeSubmission(userInput);
        } else {
            handleChatMessage(userInput);
        }
    }

    function initializeChat() {
        const savedTheme = localStorage.getItem(THEME_KEY) || window.DEFAULT_THEME || 'catppuccin';
        applyTheme(savedTheme);
        const token = sessionStorage.getItem(TOKEN_KEY);
        conversationHistory = [];

        if (token) {
            chatState = 'chatting';
            chatInput.classList.remove('password-mask');
            const welcomeMsg = uiText('chat.welcome_back');
            addMessage(welcomeMsg, 'bot');
            conversationHistory.push({role: 'assistant', content: welcomeMsg});
            setInputState(true, uiText('chat.ask_placeholder'));
        } else {
            chatState = 'awaiting_code';
            chatInput.classList.add('password-mask');
            const welcomeMessage = chatWindow.dataset.welcome
                || uiText('chat.welcome_fallback');
            addMessage(welcomeMessage, 'bot');
            setInputState(true, uiText('chat.code_placeholder'));
        }
    }

    chatForm.addEventListener('submit', handleFormSubmit);
    modalClose.addEventListener('click', hideNotice);
    modal.addEventListener('click', handleModalClick);
    modal.addEventListener('keydown', handleModalKey);
    initializeChat();

    console.log("Recruiter (Chat) View Specifics Initialized with History.");

    window.cleanupRecruiterView = () => {
        console.log("Running cleanup for Recruiter Chat view...");
        chatForm.removeEventListener('submit', handleFormSubmit);
        modalClose.removeEventListener('click', hideNotice);
        modal.removeEventListener('click', handleModalClick);
        modal.removeEventListener('keydown', handleModalKey);
    };
};
