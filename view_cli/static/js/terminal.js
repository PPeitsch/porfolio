// The function is now defined on the window object to be called from selector.js
window.initializeCliView = function(callbacks) {
    const cliWindow = document.getElementById("cli-window");
    if (!cliWindow || cliWindow.dataset.viewInitialized) {
        return;
    }
    cliWindow.dataset.viewInitialized = "true";
    console.log("Initializing CLI View Specifics...");

    // Initialize the draggable window functionality, passing the onClose callback
    const windowControls = initializeDraggableWindow({
        windowId: "cli-window",
        titleBarId: "cli-title-bar",
        closeBtnId: "cli-close",
        minimizeBtnId: "cli-minimize",
        maximizeBtnId: "cli-maximize",
        onClose: callbacks.onClose,
    });

    // --- DOM Element Selection for Terminal ---
    const terminalContent = document.getElementById("terminal-content");
    const outputDiv = terminalContent.querySelector("#output");
    const inputElem = terminalContent.querySelector("#input");
    const promptSpan = terminalContent.querySelector("#prompt");

    if (!terminalContent || !outputDiv || !inputElem || !promptSpan) {
        console.error("One or more essential terminal content elements are missing!");
        return;
    }

    // --- Terminal Logic ---
    const commandHistory = [];
    let historyIndex = -1;
    let isFetching = false;

    function writeOutput(text, className = null) {
        const line = document.createElement("div");
        line.innerHTML = text.replace(/<link>(.*?)<\/link>/g, (match, url) => {
            const isMail = url.startsWith("mailto:");
            if (isMail || url.startsWith("http")) {
                const cleanUrl = url.replace("mailto:", "");
                const linkText = cleanUrl.length > 50 ? cleanUrl.substring(0, 47) + "..." : cleanUrl;
                return `<a href="${url}" ${!isMail ? 'target="_blank" rel="noopener noreferrer"' : ""} class="terminal-link" title="${cleanUrl}">${linkText}</a>`;
            }
            return url;
        });
        if (className) { line.classList.add(className); }
        outputDiv.appendChild(line);
        scrollToBottom();
    }
    function clearScreen() { outputDiv.innerHTML = ""; }
    function scrollToBottom() { outputDiv.scrollTop = outputDiv.scrollHeight; }

    async function processCommand(commandLine) {
        writeOutput(promptSpan.textContent + commandLine, "echo-command");
        if (commandLine) { commandHistory.push(commandLine); }
        historyIndex = commandHistory.length;

        const parts = commandLine.trim().split(/\s+/);
        const command = parts[0].toLowerCase();
        const args = parts.slice(1);

        // --- Local Command Interceptor ---
        const localCommands = {
            'maximize': windowControls.maximize,
            'minimize': windowControls.minimize,
            'restore': () => { if (cliWindow.classList.contains('minimized')) windowControls.minimize(); else windowControls.maximize(); },
            'close': windowControls.close,
            'exit': windowControls.close,
            'win-reset': windowControls.reset,
            'clear': clearScreen,
        };

        if (localCommands[command]) {
            localCommands[command]();
            inputElem.focus();
            return;
        }

        if (command === 'date') {
            writeOutput(new Date().toString());
            inputElem.focus();
            return;
        }

        if (command === 'echo') {
            writeOutput(args.join(' '));
            inputElem.focus();
            return;
        }

        if (isFetching) return;
        isFetching = true;
        inputElem.disabled = true;

        try {
            const response = await fetch(`/cli/api/command/${encodeURIComponent(commandLine)}`);
            if (!response.ok) {
                let errorMsg = `Server error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) { errorMsg = `Server error: ${errorData.error}`; }
                } catch (e) {}
                throw new Error(errorMsg);
            }
            const data = await response.json();
            if (data.output && data.output.length > 0) { data.output.forEach((line) => writeOutput(line)); }
            if (data.error) { writeOutput(data.error, "error-message"); }
        } catch (error) {
            console.error("Error processing command:", error);
            writeOutput(`Error: ${error.message}`, "error-message");
        } finally {
            isFetching = false;
            inputElem.disabled = false;
            setTimeout(() => inputElem.focus(), 0);
            scrollToBottom();
        }
    }

    inputElem.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            const commandLine = inputElem.value.trim();
            inputElem.value = "";
            processCommand(commandLine);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            if (commandHistory.length > 0 && historyIndex > 0) {
                historyIndex--;
                inputElem.value = commandHistory[historyIndex];
                inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
            }
        } else if (event.key === "ArrowDown") {
            event.preventDefault();
            if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
                historyIndex++;
                inputElem.value = commandHistory[historyIndex];
                inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
            } else if (historyIndex === commandHistory.length - 1) {
                historyIndex++;
                inputElem.value = "";
            }
        } else if (event.key === "l" && event.ctrlKey) {
            event.preventDefault();
            processCommand("clear");
        }
    });

    outputDiv.addEventListener("click", (event) => { if (event.target.tagName !== "A") { inputElem.focus(); } });

    // --- Initial Setup ---
    clearScreen();
    writeOutput("Welcome to the PPeitsch CLI Portfolio!");
    writeOutput("Type 'help' for a list of available commands.");
    writeOutput("You can drag this window by its title bar.");
    writeOutput("");
    inputElem.focus();
    console.log("CLI View Specifics Initialized.");
}
