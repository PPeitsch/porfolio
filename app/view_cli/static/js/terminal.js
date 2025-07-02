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
  let authState = 'awaiting_password';
  let promptConfig = { template: "{user}@{host}:~ $", user: "user", host: "localhost" };
  const commandHistory = [];
  let historyIndex = -1;
  let isFetching = false;
  const TOKEN_KEY = 'app_access_token';
  const THEME_KEY = 'cli_theme';
  const availableCommands = [
      'help', 'whoami', 'skills', 'contact', 'links', 'ls', 'filter', 'show', 'open',
      'man', 'theme', 'maximize', 'minimize', 'restore', 'win-reset', 'clear', 'date', 'echo',
      'uname', 'neofetch', 'exit', 'close'
  ];
  const availableThemes = ['dracula', 'light', 'solarized', 'gruvbox', 'catppuccin'];

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

  function updatePrompt() {
      const { template, user, host } = promptConfig;
      const promptText = template.replace("{user}", user).replace("{host}", host);
      promptSpan.textContent = promptText;
  }

  function showLoginPrompt() {
      clearScreen();
      promptSpan.textContent = "password:";
      inputElem.classList.add('password-mask');
      writeOutput("Authentication required for CLI access.");
  }

  function showAuthenticatedPrompt() {
      updatePrompt();
      inputElem.classList.remove('password-mask');
      clearScreen();
      writeOutput("Welcome to the PPeitsch CLI Portfolio!");
      writeOutput("Type 'help' for a list of available commands.");
      writeOutput("Type 'theme light' or 'theme gruvbox' to change the look.");
      writeOutput("");
  }

  async function processCommand(commandLine) {
      if (!commandLine.trim() && authState === 'authenticated') {
          writeOutput(promptSpan.textContent + " ");
          return;
      }

      if (authState === 'awaiting_password') {
          const code = commandLine.trim();
          if (!code) return;

          isFetching = true;
          inputElem.disabled = true;

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
              if (data.prompt) { promptConfig = data.prompt; }
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

      writeOutput(promptSpan.textContent + " " + commandLine, "echo-command");
      if (commandLine) { commandHistory.push(commandLine); }
      historyIndex = commandHistory.length;

      const parts = commandLine.trim().split(/\s+/);
      const command = parts[0].toLowerCase();
      const args = parts.slice(1);

      const localCommands = {
          'theme': (args) => {
              const themeName = (args[0] || '').toLowerCase();
              if (!themeName) {
                  const currentTheme = localStorage.getItem(THEME_KEY) || 'dracula';
                  writeOutput(`Current theme: '${currentTheme}'.`, 'info-message');
                  writeOutput(`Available themes: ${availableThemes.join(', ')}`);
                  return;
              }

              if (availableThemes.includes(themeName)) {
                  cliWindow.dataset.theme = themeName;
                  localStorage.setItem(THEME_KEY, themeName);
                  writeOutput(`Theme set to '${themeName}'.`, 'info-message');
              } else {
                  writeOutput(`Error: Theme '${themeName}' not found. Available: ${availableThemes.join(', ')}`, 'error-message');
              }
          },
          'maximize': windowControls.maximize,
          'minimize': windowControls.minimize,
          'restore': () => { if (cliWindow.classList.contains('minimized')) windowControls.minimize(); else windowControls.maximize(); },
          'close': windowControls.close,
          'exit': windowControls.close,
          'win-reset': windowControls.reset,
          'clear': clearScreen,
          'date': () => writeOutput(new Date().toString()),
          'echo': (args) => writeOutput(args.join(' ')),
      };

      if (localCommands[command]) {
          localCommands[command](args);
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
              headers: { 'Authorization': `Bearer ${token}` }
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
              try { const errorData = await response.json(); if (errorData && errorData.error) { errorMsg = `Server error: ${errorData.error}`; } } catch (e) {}
              throw new Error(errorMsg);
          }

          const data = await response.json();
          if (data.prompt) {
              promptConfig = data.prompt;
              updatePrompt();
          }
          if (data.output && data.output.length > 0) { data.output.forEach((line) => writeOutput(line)); }
          if (data.error) { writeOutput(data.error, "error-message"); }
          if (data.action === 'open_url' && data.url) { window.open(data.url, '_blank'); }

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

  function handleTabCompletion() {
      const currentInput = inputElem.value;
      const parts = currentInput.split(' ');
      const currentWord = parts[parts.length - 1];


      if (parts.length === 1) { // Completing command
          const matchingCommands = availableCommands.filter(cmd => cmd.startsWith(currentWord));
          if (matchingCommands.length === 1) {
              inputElem.value = matchingCommands[0] + ' ';
          } else if (matchingCommands.length > 1) {
              writeOutput(promptSpan.textContent + " " + currentInput, "echo-command");
              writeOutput(matchingCommands.join('   '), 'completion-options');
          }
      } else if (parts.length === 2 && parts[0] === 'theme') { // Completing theme
          const matchingThemes = availableThemes.filter(theme => theme.startsWith(currentWord));
          if (matchingThemes.length === 1) {
              inputElem.value = parts[0] + ' ' + matchingThemes[0];
          }
      }
  }

  inputElem.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
          event.preventDefault();
          const commandLine = inputElem.value;
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
          if (authState === 'authenticated') { processCommand("clear"); }
      } else if (event.key === "Tab") {
          if (authState === 'authenticated') {
              event.preventDefault();
              handleTabCompletion();
          }
      }
  });

  outputDiv.addEventListener("click", (event) => { if (event.target.tagName !== "A") { inputElem.focus(); } });

  function initializeTerminal() {
      const savedTheme = localStorage.getItem(THEME_KEY) || 'dracula';
      if (availableThemes.includes(savedTheme)) {
          cliWindow.dataset.theme = savedTheme;
      }

      const token = sessionStorage.getItem(TOKEN_KEY);
      if (token) {
          authState = 'authenticated';
          // Run a harmless command to get latest prompt config on load
          processCommand('help');
          // Clear the output from the initial help command
          setTimeout(() => { clearScreen(); showAuthenticatedPrompt(); }, 100);
      } else {
          authState = 'awaiting_password';
          showLoginPrompt();
      }
      inputElem.focus();
  }

  initializeTerminal();
  console.log("CLI View Specifics Initialized with Auth Flow.");
}
