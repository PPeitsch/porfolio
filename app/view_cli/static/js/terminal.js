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

  // Output is plain text: only <link>url</link> markers become links, so
  // texts like "<name>" are shown as written and never parsed as HTML.
  function writeOutput(text, className = null) {
      const line = document.createElement("div");
      const linkPattern = /<link>(.*?)<\/link>/g;
      let last = 0;
      let match;
      while ((match = linkPattern.exec(text)) !== null) {
          line.appendChild(document.createTextNode(text.slice(last, match.index)));
          line.appendChild(createLink(match[1]));
          last = linkPattern.lastIndex;
      }
      line.appendChild(document.createTextNode(text.slice(last)));
      if (className) { line.classList.add(className); }
      outputDiv.appendChild(line);
      scrollToBottom();
  }

  function createLink(url) {
      const isMail = url.startsWith("mailto:");
      if (!isMail && !/^https?:\/\//.test(url)) {
          return document.createTextNode(url);
      }
      const cleanUrl = url.replace("mailto:", "");
      const link = document.createElement("a");
      link.href = url;
      link.className = "terminal-link";
      link.title = cleanUrl;
      link.textContent = cleanUrl.length > 50 ? cleanUrl.substring(0, 47) + "..." : cleanUrl;
      if (!isMail) {
          link.target = "_blank";
          link.rel = "noopener noreferrer";
      }
      return link;
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
      writeOutput(uiText("cli.auth_required"));
  }

  function showAuthenticatedPrompt() {
      updatePrompt();
      inputElem.classList.remove('password-mask');
      clearScreen();
      writeOutput(cliWindow.dataset.welcome || uiText("cli.welcome_fallback"));
      writeOutput(uiText("cli.hint_help"));
      writeOutput(uiText("cli.hint_theme"));
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

              if (response.status === 429) {
                  const data = await response.json().catch(() => ({}));
                  const minutes = Math.max(1, Math.ceil((Number(data.retry_after) || 60) / 60));
                  writeOutput(uiText("cli.too_many_attempts", { minutes }), "error-message");
                  return;
              }
              if (!response.ok) {
                  const errorData = await response.json();
                  throw new Error(errorData.error || uiText('cli.permission_denied'));
              }

              const data = await response.json();
              sessionStorage.setItem(TOKEN_KEY, data.token);
              if (data.prompt) { promptConfig = data.prompt; }
              authState = 'authenticated';
              showAuthenticatedPrompt();

          } catch (error) {
              writeOutput(uiText("cli.permission_denied"), "error-message");
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
                  const currentTheme = localStorage.getItem(THEME_KEY) || window.DEFAULT_THEME || 'catppuccin';
                  writeOutput(uiText('cli.theme_current', { theme: currentTheme }), 'info-message');
                  writeOutput(uiText('cli.theme_available', { themes: availableThemes.join(', ') }));
                  return;
              }

              if (availableThemes.includes(themeName)) {
                  // The whole page and every open window, as the dock button does.
                  document.documentElement.dataset.theme = themeName;
                  document.querySelectorAll('.os-window').forEach(win => {
                      win.dataset.theme = themeName;
                  });
                  localStorage.setItem(THEME_KEY, themeName);
                  writeOutput(uiText('cli.theme_set', { theme: themeName }), 'info-message');
              } else {
                  writeOutput(uiText('cli.theme_not_found', { theme: themeName, themes: availableThemes.join(', ') }), 'error-message');
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
          writeOutput(uiText("cli.no_token"), "error-message");
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
               writeOutput(uiText("cli.session_expired"), "error-message");
               showLoginPrompt();
               return;
          }

          if (!response.ok) {
              let errorMsg = uiText('cli.server_error', { error: response.status });
              try { const errorData = await response.json(); if (errorData && errorData.error) { errorMsg = uiText('cli.server_error', { error: errorData.error }); } } catch (e) {}
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
      const savedTheme = localStorage.getItem(THEME_KEY) || window.DEFAULT_THEME || 'catppuccin';
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
