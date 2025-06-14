// The function is now defined on the window object to be called from selector.js
window.initializeRecruiterView = function(callbacks) {
    const chatWindow = document.getElementById("chat-window");
    if (!chatWindow || chatWindow.dataset.viewInitialized) {
        return;
    }
    chatWindow.dataset.viewInitialized = "true";
    console.log("Initializing Recruiter (Chat) View Specifics...");

    // Initialize the draggable window functionality, passing the onClose callback
    const windowControls = initializeDraggableWindow({
        windowId: "chat-window",
        titleBarId: "chat-title-bar",
        closeBtnId: "chat-close",
        minimizeBtnId: "chat-minimize",
        maximizeBtnId: "chat-maximize",
        onClose: callbacks.onClose,
    });

    // --- DOM Element Selection for Chat ---
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('chat-send-button');

    if (!chatMessages || !chatForm || !chatInput || !sendButton) {
        console.error("One or more Chat UI content elements are missing!");
        return;
    }

    let isLoading = false;

    // Simple Markdown to HTML parser
    function parseMarkdown(text) {
        let html = text.replace(/\n/g, '<br>');
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
        html = html.replace(/(\<li\>.*\<\/li\>)/gs, '<ul>$1</ul>');
        return html;
    }

    function addMessage(text, sender, isTyping = false) {
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', sender);

        if (isTyping) {
            bubble.classList.add('typing');
            bubble.setAttribute('id', 'typing-indicator');
            bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        } else {
            bubble.innerHTML = parseMarkdown(text);
        }

        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        const userMessage = chatInput.value.trim();

        if (!userMessage || isLoading) return;

        isLoading = true;
        chatInput.value = '';
        chatInput.disabled = true;
        sendButton.disabled = true;

        addMessage(userMessage, 'user');
        addMessage('', 'bot', true); // Show typing indicator

        try {
            const response = await fetch('/recruiter/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) typingIndicator.remove();

            if (!response.ok) {
                let errorMsg = `HTTP error! Status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.reply || errorData.error || `Server error: ${response.statusText}`;
                } catch(e) {
                    // Response was not JSON
                }
                throw new Error(errorMsg);
            }

            const data = await response.json();
            addMessage(data.reply, 'bot');

        } catch (error) {
            console.error('Chat API Error:', error);
            const typingIndicator = document.getElementById('typing-indicator');
            if (typingIndicator) typingIndicator.remove();
            addMessage(`Sorry, an error occurred: ${error.message}`, 'bot');
        } finally {
            isLoading = false;
            chatInput.disabled = false;
            sendButton.disabled = false;
            chatInput.focus();
        }
    }

    chatForm.addEventListener('submit', handleFormSubmit);

    // Initial greeting from the bot
    setTimeout(() => {
        const initialGreeting = "Hello! I'm an AI assistant for Pablo Peitsch. How can I help you today?";
        addMessage(initialGreeting, 'bot');
        chatInput.focus();
    }, 600);

    console.log("Recruiter (Chat) View Specifics Initialized.");

    window.cleanupRecruiterView = () => {
        console.log("Running cleanup for Recruiter Chat view...");
        chatForm.removeEventListener('submit', handleFormSubmit);
    };
}
