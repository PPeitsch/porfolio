(function () {
    // Ensure this script runs only once and finds the necessary elements
    const cliWindow = document.getElementById("cli-window");
    if (!cliWindow || cliWindow.dataset.initialized) {
        return;
    }
    cliWindow.dataset.initialized = "true";

    console.log("Attempting to initialize CLI Window Interface...");

    // --- DOM Element Selection ---
    const titleBar = document.getElementById("cli-title-bar");
    const terminal = document.getElementById("terminal");
    const outputDiv = terminal.querySelector("#output");
    const inputElem = terminal.querySelector("#input");
    const promptSpan = terminal.querySelector("#prompt");

    // Check for essential elements
    if (!titleBar || !terminal || !outputDiv || !inputElem || !promptSpan) {
        console.error("One or more essential CLI elements are missing!");
        return;
    }

    // --- Window Dragging Logic ---
    let isDragging = false;
    let offsetX, offsetY;

    function onMouseDown(e) {
        // Only drag with the primary mouse button and if the target is the title bar itself
        if (e.button !== 0 || e.target.classList.contains("control-btn")) {
            return;
        }

        isDragging = true;
        // Calculate the initial offset from the top-left corner of the window
        offsetX = e.clientX - cliWindow.offsetLeft;
        offsetY = e.clientY - cliWindow.offsetTop;

        // Add listeners to the document to capture mouse movement anywhere on the page
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
        document.addEventListener("mouseleave", onMouseUp); // Stop dragging if mouse leaves window

        titleBar.style.cursor = "grabbing"; // Change cursor to indicate dragging
        cliWindow.style.userSelect = "none"; // Prevent text selection while dragging
    }

    function onMouseMove(e) {
        if (!isDragging) return;

        // Calculate new position
        let newX = e.clientX - offsetX;
        let newY = e.clientY - offsetY;

        // Get viewport dimensions to constrain the window
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const windowWidth = cliWindow.offsetWidth;
        const windowHeight = cliWindow.offsetHeight;

        // Constrain the window within the viewport
        newX = Math.max(0, Math.min(newX, viewportWidth - windowWidth));
        newY = Math.max(0, Math.min(newY, viewportHeight - windowHeight));

        cliWindow.style.left = `${newX}px`;
        cliWindow.style.top = `${newY}px`;
    }

    function onMouseUp() {
        if (!isDragging) return;
        isDragging = false;

        // Clean up event listeners
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.removeEventListener("mouseleave", onMouseUp);

        titleBar.style.cursor = "grab"; // Revert cursor
        cliWindow.style.userSelect = ""; // Re-enable text selection
    }

    // Attach the initial event listener to the title bar
    titleBar.addEventListener("mousedown", onMouseDown);

    // --- Terminal Logic (adapted from original file) ---
    const commandHistory = [];
    let historyIndex = -1;
    let isFetching = false;

    function writeOutput(text, className = null) {
        const line = document.createElement("div");
        line.innerHTML = text.replace(/<link>(.*?)<\/link>/g, (match, url) => {
            const isMail = url.startsWith("mailto:");
            if (isMail || url.startsWith("http")) {
                return `<a href="${url}" ${
                    !isMail ? 'target="_blank" rel="noopener noreferrer"' : ""
                } class="terminal-link">${url.replace("mailto:", "")}</a>`;
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
            const response = await fetch(
                `/cli/api/command/${encodeURIComponent(commandLine)}`
            );
            if (!response.ok) {
                let errorMsg = `Server error: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.error) {
                        errorMsg = `Server error: ${errorData.error}`;
                    }
                } catch (e) {
                    /* Ignore if response is not JSON */
                }
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
                inputElem.setSelectionRange(
                    inputElem.value.length,
                    inputElem.value.length
                );
            }
        } else if (event.key === "ArrowDown") {
            event.preventDefault();
            if (
                commandHistory.length > 0 &&
                historyIndex < commandHistory.length - 1
            ) {
                historyIndex++;
                inputElem.value = commandHistory[historyIndex];
                inputElem.setSelectionRange(
                    inputElem.value.length,
                    inputElem.value.length
                );
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
