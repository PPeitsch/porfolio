// Wrap entire logic in a function to be called after loading
function initializeTerminalInterface() {
    console.log("Attempting to initialize Terminal Interface..."); // Debug log

    const terminal = document.getElementById('terminal');
    if (!terminal) {
        console.error("Terminal container (#terminal) not found in loaded HTML!");
        return; // Stop if the main container isn't there
    }
    // Find elements *within* the terminal container
    const outputDiv = terminal.querySelector('#output');
    const inputLine = terminal.querySelector('#input-line');
    const promptSpan = terminal.querySelector('#prompt');
    const inputElem = terminal.querySelector('#input');

    if (!outputDiv || !inputLine || !promptSpan || !inputElem) {
         console.error("One or more essential terminal child elements (#output, #input-line, #prompt, #input) are missing!");
         return; // Stop if core elements aren't found
    }

    const commandHistory = [];
    let historyIndex = -1;
    let isFetching = false;

    // --- Helper Functions ---
    function writeOutput(text, className = null) {
        const line = document.createElement('div');
        // Parse <link> tags into clickable anchors
        line.innerHTML = text.replace(/<link>(.*?)<\/link>/g, (match, url) => {
            // Basic check to ensure it looks like a URL before creating link
            if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="terminal-link">${url}</a>`;
            }
            return url; // Return text if not a valid link format
        });

        if (className) {
            line.classList.add(className);
        }
        outputDiv.appendChild(line);
        scrollToBottom();
    }

    function clearScreen() {
        outputDiv.innerHTML = '';
    }

    function scrollToBottom() {
        outputDiv.scrollTop = outputDiv.scrollHeight;
    }

    async function processCommand(commandLine) {
        if (isFetching) return;
        isFetching = true;
        inputElem.disabled = true;

        writeOutput(promptSpan.textContent + commandLine, 'echo-command');
        if (commandLine) { // Only add non-empty commands to history
            commandHistory.push(commandLine);
        }
        historyIndex = commandHistory.length; // Reset index AFTER push

        if (commandLine.toLowerCase() === 'clear') {
            clearScreen();
            isFetching = false;
            inputElem.disabled = false;
            inputElem.focus();
            return;
        }

        // Send command to backend API (Note the /cli prefix)
        try {
            const response = await fetch(`/cli/api/command/${encodeURIComponent(commandLine)}`);
            if (!response.ok) {
                 // Try to get error message from server response body
                 let errorMsg = `Server error: ${response.status}`;
                 try {
                     const errorData = await response.json();
                     if(errorData && errorData.error) {
                         errorMsg = `Server error: ${errorData.error}`;
                     }
                 } catch(e) { /* Ignore if response is not JSON */ }
                 throw new Error(errorMsg);
            }
            const data = await response.json();

            if (data.output && data.output.length > 0) {
                data.output.forEach(line => writeOutput(line));
            }
            if (data.error) {
                writeOutput(data.error, 'error-message');
            }

        } catch (error) {
            console.error('Error processing command:', error);
            writeOutput(`Error: ${error.message}`, 'error-message');
        } finally {
            isFetching = false;
            inputElem.disabled = false;
            // Small timeout to ensure focus happens after potential DOM updates
            setTimeout(() => inputElem.focus(), 0);
            scrollToBottom();
        }
    }

    // --- Event Listeners ---
    inputElem.addEventListener('keydown', (event) => {
        // Use key property (modern) instead of keyCode
        if (event.key === 'Enter') {
            event.preventDefault();
            const commandLine = inputElem.value.trim();
            inputElem.value = ''; // Clear input immediately
            processCommand(commandLine);
        } else if (event.key === 'ArrowUp') {
             event.preventDefault();
             if (commandHistory.length > 0 && historyIndex > 0) {
                 historyIndex--;
                 inputElem.value = commandHistory[historyIndex];
                 inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
             }
         } else if (event.key === 'ArrowDown') {
             event.preventDefault();
             if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
                 historyIndex++;
                 inputElem.value = commandHistory[historyIndex];
                 inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
             } else if (historyIndex === commandHistory.length - 1) {
                 historyIndex++; // Move past the last command
                 inputElem.value = ''; // Clear input
             }
         } else if (event.key === 'Tab') {
             event.preventDefault();
             // TODO: Implement tab completion
             console.log("Tab completion not implemented.");
         } else if (event.key === 'l' && event.ctrlKey) {
             // Optional: Ctrl+L to clear screen (like Linux terminal)
             event.preventDefault();
             processCommand('clear');
         }
    });

    // Focus input when clicking inside the terminal output area
    outputDiv.addEventListener('click', (event) => {
        // Only focus if the click wasn't on a link
        if (event.target.tagName !== 'A') {
             inputElem.focus();
        }
    });


    // --- Initial Setup ---
    clearScreen(); // Start with a clean slate
    writeOutput("Welcome to PPeitsch CLI Portfolio!");
    writeOutput("Type 'help' for a list of commands.");
    writeOutput(""); // Add an empty line
    inputElem.focus();
    console.log("Terminal Interface Initialized and ready.");

} // End of initializeTerminalInterface

// Make the initializer globally accessible IF NEEDED by selector.js
// If using modules later, this would be exported.
window.initializeTerminalInterface = initializeTerminalInterface;