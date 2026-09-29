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

    if (!chatMessages || !chatForm || !chatInput || !sendButton) {
        console.error("One or more Chat UI content elements are missing!");
        return;
    }

    let isLoading = false;
    let chatState = 'awaiting_code';
    const TOKEN_KEY = 'app_access_token';
    const THEME_KEY = 'cli_theme';
    let conversationHistory = [];

    function applyTheme(themeName) {
        chatWindow.dataset.theme = themeName;
    }

    function addMessage(text, sender, isTyping = false) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);

        if (isTyping) {
            bubble.classList.add('typing');
            bubble.setAttribute('id', 'typing-indicator');
            bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        } else {
            bubble.innerHTML = renderChatMarkdown(text);
        }


        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function setInputState(enabled, placeholder) {
        chatInput.disabled = !enabled;
        sendButton.disabled = !enabled;
        chatInput.placeholder = placeholder;
        if (enabled) chatInput.focus();
    }

    async function handleCodeSubmission(code) {
        isLoading = true;
        setInputState(false, 'Verifying code...');
        addMessage('', 'bot', true);

        try {
            const response = await fetch('/auth/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code: code}),
            });

            chatWindow.querySelector('#typing-indicator')?.remove();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Invalid code.');
            }

            const data = await response.json();
            sessionStorage.setItem(TOKEN_KEY, data.token);
            chatState = 'chatting';
            chatInput.classList.remove('password-mask');
            const welcomeMsg = "Access granted! Thank you. How can I help you?";
            addMessage(welcomeMsg, 'bot');
            conversationHistory.push({role: 'assistant', content: welcomeMsg});
            setInputState(true, 'Ask about my skills or projects...');

        } catch (error) {
            addMessage(`Sorry, that's not the correct code. Please try again.`, 'bot');
            setInputState(true, 'Enter access code...');
        } finally {
            isLoading = false;
        }
    }

    async function handleChatMessage(message) {
        isLoading = true;
        setInputState(false, 'Thinking...');
        addMessage(message, 'user');
        conversationHistory.push({role: 'user', content: message});
        addMessage('', 'bot', true);

        const token = sessionStorage.getItem(TOKEN_KEY);
        if (!token) {
            chatWindow.querySelector('#typing-indicator')?.remove();
            addMessage("Your session has expired. Please re-enter the access code.", 'bot');
            chatState = 'awaiting_code';
            chatInput.classList.add('password-mask');
            conversationHistory = [];
            setInputState(true, 'Enter access code...');
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

            chatWindow.querySelector('#typing-indicator')?.remove();

            if (response.status === 401) {
                sessionStorage.removeItem(TOKEN_KEY);
                addMessage("Your session has expired. Please enter the access code again.", 'bot');
                chatState = 'awaiting_code';
                chatInput.classList.add('password-mask');
                conversationHistory = [];
                setInputState(true, 'Enter access code...');
                return;
            }
            if (!response.ok) throw new Error('The AI assistant is currently unavailable.');

            const data = await response.json();
            addMessage(data.reply, 'bot');
            conversationHistory = data.history || [];

        } catch (error) {
            chatWindow.querySelector('#typing-indicator')?.remove();
            addMessage(`Sorry, an error occurred: ${error.message}`, 'bot');
            conversationHistory.pop();
        } finally {
            isLoading = false;
            setInputState(true, 'Ask another question...');
        }
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        const userInput = chatInput.value.trim();
        if (!userInput || isLoading) return;
        chatInput.value = '';

        if (chatState === 'awaiting_code') {
            handleCodeSubmission(userInput);
        } else {
            handleChatMessage(userInput);
        }
    }

    function initializeChat() {
        const savedTheme = localStorage.getItem(THEME_KEY) || 'dracula';
        applyTheme(savedTheme);
        const token = sessionStorage.getItem(TOKEN_KEY);
        conversationHistory = [];

        if (token) {
            chatState = 'chatting';
            chatInput.classList.remove('password-mask');
            const welcomeMsg = "Welcome back! How can I assist you?";
            addMessage(welcomeMsg, 'bot');
            conversationHistory.push({role: 'assistant', content: welcomeMsg});
            setInputState(true, 'Ask about my skills or projects...');
        } else {
            chatState = 'awaiting_code';
            chatInput.classList.add('password-mask');
            const welcomeMessage = chatWindow.dataset.welcome
                || "Hello! This chat requires an access code. Please enter it to continue.";
            addMessage(welcomeMessage, 'bot');
            setInputState(true, 'Enter access code...');
        }
    }

    chatForm.addEventListener('submit', handleFormSubmit);
    initializeChat();

    console.log("Recruiter (Chat) View Specifics Initialized with History.");

    window.cleanupRecruiterView = () => {
        console.log("Running cleanup for Recruiter Chat view...");
        chatForm.removeEventListener('submit', handleFormSubmit);
    };
};
