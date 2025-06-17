// The function is now defined on the window object to be called from selector.js
window.initializeCliView = function(callbacks) {
   const cliWindow = document.getElementById("cli-window");
   if (!cliWindow || cliWindow.dataset.viewInitialized) {
       return;
   }
   cliWindow.dataset.viewInitialized = "true";
   console.log("Initializing CLI View Specifics...");

   const windowControls = initializeDraggableWindow({
       windowId: "cli-window",
       titleBarId: "cli-title-bar",
       closeBtnId: "cli-close",
       minimizeBtnId: "cli-minimize",
       maximizeBtnId: "cli-maximize",
       onClose: callbacks.onClose,
   });

   const terminalContent = document.getElementById("terminal-content");
   const outputDiv = terminalContent.querySelector("#output");
   const inputElem = terminalContent.querySelector("#input");
   const promptSpan = terminalContent.querySelector("#prompt");

   if (!terminalContent || !outputDiv || !inputElem || !promptSpan) {
       console.error("One or more essential terminal content elements are missing!");
       return;
   }

   // --- State Management ---
   let authState = 'awaiting_password'; // 'awaiting_password' or 'authenticated'
   const commandHistory = [];
   let historyIndex = -1;
   let isFetching = false;
   const TOKEN_KEY = 'app_access_token';

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

   function showLoginPrompt() {
       clearScreen();
       promptSpan.textContent = "password:";
       inputElem.classList.add('password-mask'); // Add the CSS class
       writeOutput("Authentication required for CLI access.");
   }

   function showAuthenticatedPrompt() {
       promptSpan.textContent = "portfolio:~ $";
       inputElem.classList.remove('password-mask'); // Remove the CSS class
       clearScreen();
       writeOutput("Welcome to the PPeitsch CLI Portfolio!");
       writeOutput("Type 'help' for a list of available commands.");
       writeOutput("You can drag this window by its title bar.");
       writeOutput("");
   }

   async function processCommand(commandLine) {
       if (authState === 'awaiting_password') {
           const code = commandLine.trim();
           if (!code) return; // Ignore empty submissions

           isFetching = true;
           inputElem.disabled = true;
           // We no longer write the fake password to the output to avoid clutter and potential security issues.
           // The user sees what they type in the input line itself.

           try {
               const response = await fetch('/auth/verify', {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify({ code: code }),
               });

               if (!response.ok) {
                   const errorData = await response.json();
                   throw new Error(errorData.error || 'Invalid code.');
               }

               const data = await response.json();
               sessionStorage.setItem(TOKEN_KEY, data.token);
               authState = 'authenticated';
               showAuthenticatedPrompt();

           } catch (error) {
               writeOutput(`Permission denied, please try again.`, "error-message");
           } finally {
               isFetching = false;
               inputElem.value = '';
               inputElem.disabled = false;
               setTimeout(() => inputElem.focus(), 0);
           }
           return;
       }

       // --- Authenticated command processing ---
       writeOutput(promptSpan.textContent + " " + commandLine, "echo-command");
       if (commandLine) { commandHistory.push(commandLine); }
       historyIndex = commandHistory.length;

       const parts = commandLine.trim().split(/\s+/);
       const command = parts[0].toLowerCase();
       const args = parts.slice(1);

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

       const token = sessionStorage.getItem(TOKEN_KEY);
       if (!token) {
           writeOutput("Authentication error: Session token not found. Please refresh.", "error-message");
           authState = 'awaiting_password';
           showLoginPrompt();
           isFetching = false;
           inputElem.disabled = false;
           return;
       }

       try {
           const response = await fetch(`/cli/api/command/${encodeURIComponent(commandLine)}`, {
               headers: {
                   'Authorization': `Bearer ${token}`
               }
           });

           if (response.status === 401) {
                sessionStorage.removeItem(TOKEN_KEY);
                authState = 'awaiting_password';
                writeOutput("Session expired. Please re-authenticate.", "error-message");
                showLoginPrompt();
                return;
           }

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
           if (authState === 'authenticated') {
               isFetching = false;
               inputElem.disabled = false;
               setTimeout(() => inputElem.focus(), 0);
           }
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
           if (authState === 'authenticated') {
               event.preventDefault();
               if (commandHistory.length > 0 && historyIndex > 0) {
                   historyIndex--;
                   inputElem.value = commandHistory[historyIndex];
                   inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
               }
           }
       } else if (event.key === "ArrowDown") {
           if (authState === 'authenticated') {
               event.preventDefault();
               if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
                   historyIndex++;
                   inputElem.value = commandHistory[historyIndex];
                   inputElem.setSelectionRange(inputElem.value.length, inputElem.value.length);
               } else if (historyIndex === commandHistory.length - 1) {
                   historyIndex++;
                   inputElem.value = "";
               }
           }
       } else if (event.key === "l" && event.ctrlKey) {
           event.preventDefault();
           if (authState === 'authenticated') {
               processCommand("clear");
           }
       }
   });

   outputDiv.addEventListener("click", (event) => { if (event.target.tagName !== "A") { inputElem.focus(); } });

   // --- Initial Setup ---
   function initializeTerminal() {
       const token = sessionStorage.getItem(TOKEN_KEY);
       if (token) {
           // A more robust check could be to decode the token and check expiration.
           // For now, if a token exists, we assume the user is authenticated.
           authState = 'authenticated';
           showAuthenticatedPrompt();
       } else {
           authState = 'awaiting_password';
           showLoginPrompt();
       }
       inputElem.focus();
   }

   initializeTerminal();
   console.log("CLI View Specifics Initialized with Auth Flow.");
}
