(function () {
    const cliWindow = document.getElementById("cli-window");
    if (!cliWindow || cliWindow.dataset.initialized) {
        return;
    }
    cliWindow.dataset.initialized = "true";

    console.log("Initializing CLI Window Interface...");

    // --- DOM Element Selection ---
    const titleBar = document.getElementById("cli-title-bar");
    const terminal = document.getElementById("terminal");
    const outputDiv = terminal.querySelector("#output");
    const inputElem = terminal.querySelector("#input");
    const promptSpan = terminal.querySelector("#prompt");
    const closeBtn = document.getElementById("cli-close");
    const minimizeBtn = document.getElementById("cli-minimize");
    const maximizeBtn = document.getElementById("cli-maximize");
    const backButton = document.getElementById("back-button");

    if (!titleBar || !terminal || !closeBtn || !minimizeBtn || !maximizeBtn || !backButton) {
        console.error("One or more essential CLI or shell elements are missing!");
        return;
    }

    // --- Window State Management (Refactored for better minimize logic) ---
    let windowState = "normal"; // can be 'normal', 'maximized', 'minimized'
    let stateBeforeMinimize = "normal"; // stores the state before minimizing
    let lastPosition = { top: cliWindow.offsetTop, left: cliWindow.offsetLeft };

    // --- Window Controls Logic (Refactored) ---
    function handleClose() {
        backButton.click();
    }

    function handleMinimize() {
        if (windowState !== "minimized") {
            // Save the current state before minimizing
            stateBeforeMinimize = windowState;
            windowState = "minimized";

            // Add 'minimized' and ensure 'maximized' is removed to avoid style conflicts
            cliWindow.classList.add("minimized");
            cliWindow.classList.remove("maximized");
        } else {
            // Restore to the state it was in before minimizing
            cliWindow.classList.remove("minimized");
            windowState = stateBeforeMinimize;

            // If it was maximized before, re-apply the maximized class
            if (windowState === "maximized") {
                cliWindow.classList.add("maximized");
            }

            // Focus input for immediate use
            inputElem.focus();
        }
    }

    function handleMaximize() {
        if (windowState === "maximized") {
            cliWindow.classList.remove("maximized");
            cliWindow.style.top = `${lastPosition.top}px`;
            cliWindow.style.left = `${lastPosition.left}px`;
            windowState = "normal";
        } else {
            if (windowState === "minimized") {
                // Un-minimize before maximizing
                cliWindow.classList.remove("minimized");
            }
            lastPosition = {
                top: cliWindow.offsetTop,
                left: cliWindow.offsetLeft,
            };
            cliWindow.classList.add("maximized");
            cliWindow.style.top = "";
            cliWindow.style.left = "";
            windowState = "maximized";
        }
        inputElem.focus();
    }

    closeBtn.addEventListener("click", handleClose);
    minimizeBtn.addEventListener("click", handleMinimize);
    maximizeBtn.addEventListener("click", handleMaximize);
    titleBar.addEventListener("dblclick", handleMaximize);

    // --- Window Dragging Logic ---
    let isDragging = false;
    let offsetX, offsetY;

    function onMouseDown(e) {
        if (e.button !== 0 || e.target.classList.contains("control-btn")) {
            return;
        }
        if (windowState === "maximized") return;

        isDragging = true;
        offsetX = e.clientX - cliWindow.offsetLeft;
        offsetY = e.clientY - cliWindow.offsetTop;
        cliWindow.classList.add('is-dragging');
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
        document.addEventListener("mouseleave", onMouseUp);
    }

    function onMouseMove(e) {
        if (!isDragging) return;
        let newX = e.clientX - offsetX;
        let newY = e.clientY - offsetY;
        const viewportWidth = document.documentElement.clientWidth;
        const viewportHeight = document.documentElement.clientHeight;
        const windowWidth = cliWindow.offsetWidth;
        const windowHeight = cliWindow.offsetHeight;
        newX = Math.max(0, Math.min(newX, viewportWidth - windowWidth));
        newY = Math.max(0, Math.min(newY, viewportHeight - windowHeight));
        cliWindow.style.left = `${newX}px`;
        cliWindow.style.top = `${newY}px`;
    }

    function onMouseUp() {
        if (!isDragging) return;
        isDragging = false;
        cliWindow.classList.remove('is-dragging');
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.removeEventListener("mouseleave", onMouseUp);
    }

    titleBar.addEventListener("mousedown", onMouseDown);

    // --- Terminal Logic (Existing code, unchanged) ---
    const commandHistory = [];
    let historyIndex = -1;
    let isFetching = false;

    function writeOutput(text, className = null) {
        const line = document.createElement("div");
        line.innerHTML = text.replace(/<link>(.*?)<\/link>/g, (match, url) => {
            const isMail = url.startsWith("mailto:");
            if (isMail || url.startsWith("http")) {
                const cleanUrl = url.replace("mailto:", "");
                const linkText =
                    cleanUrl.length > 50
                        ? cleanUrl.substring(0, 47) + "..."
                        : cleanUrl;
                return `<a href="${url}" ${
                    !isMail ? 'target="_blank" rel="noopener noreferrer"' : ""
                } class="terminal-link" title="${cleanUrl}">${linkText}</a>`;
            }
            return url;
        });

        if (className) {
            line.classList.add(className);
        }
        outputDiv.appendChild(line);
        scrollToBottom();
    }

    function clearScreen() {
        outputDiv.innerHTML = "";
    }

    function scrollToBottom() {
        outputDiv.scrollTop = outputDiv.scrollHeight;
    }

    async function processCommand(commandLine) {
        if (isFetching) return;
        isFetching = true;
        inputElem.disabled = true;
        writeOutput(promptSpan.textContent + commandLine, "echo-command");
        if (commandLine) {
            commandHistory.push(commandLine);
        }
        historyIndex = commandHistory.length;
        if (commandLine.toLowerCase() === "clear") {
            clearScreen();
            isFetching = false;
            inputElem.disabled = false;
            inputElem.focus();
            return;
        }
        try {
            const response = await fetch(`/cli/api/command/${encodeURIComponent(commandLine)}`);
            if (!response.ok) {
                let errorMsg = `Server error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMsg = `Server error: ${errorData.error}`;
                    }
                } catch (e) {}
                throw new Error(errorMsg);
            }
            const data = await response.json();
            if (data.output && data.output.length > 0) {
                data.output.forEach((line) => writeOutput(line));
            }
            if (data.error) {
                writeOutput(data.error, "error-message");
            }
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

    outputDiv.addEventListener("click", (event) => {
        if (event.target.tagName !== "A") {
            inputElem.focus();
        }
    });

    // --- Initial Setup ---
    clearScreen();
    writeOutput("Welcome to the PPeitsch CLI Portfolio!");
    writeOutput("Type 'help' for a list of available commands.");
    writeOutput("You can drag this window by its title bar.");
    writeOutput("");
    inputElem.focus();
    console.log("CLI Window Interface Initialized.");
})();
