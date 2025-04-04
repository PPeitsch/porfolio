document.addEventListener('DOMContentLoaded', () => {
    const selectorContainer = document.getElementById('selector-container');
    const viewContainer = document.getElementById('view-container');
    const backButton = document.getElementById('back-button');

    const cliOption = document.getElementById('select-cli');
    const recruiterOption = document.getElementById('select-recruiter');
    const visualOption = document.getElementById('select-visual');

    let currentView = null;
    let currentCleanup = null; // Function to call for cleanup

    // --- Resource Loading/Cleanup ---
    function loadCSS(href, id) {
        if (document.getElementById(id)) return; // Already loaded
        const link = document.createElement('link');
        link.rel = 'stylesheet'; link.href = href; link.id = id;
        document.head.appendChild(link);
        console.log(`CSS loaded: ${href}`);
    }

    function loadJS(src, id, callback) {
        if (document.getElementById(id)) {
            // If script tag exists, assume script loaded, try calling callback
             if (callback && typeof window[callback] === 'function') {
                 console.log(`JS already loaded (${src}), calling ${callback}()`);
                 window[callback]();
             } else {
                  console.log(`JS already loaded (${src}), no callback or callback invalid.`);
             }
            return;
        }
        const script = document.createElement('script');
        script.src = src; script.id = id; script.async = false; // Load sequentially if needed
        script.onload = () => {
            console.log(`JS loaded: ${src}`);
            if (callback && typeof window[callback] === 'function') {
                console.log(`Calling ${callback}()`);
                window[callback]();
            } else if (callback) {
                console.warn(`JS ${src} loaded, but callback ${callback} not found or not a function.`);
            }
        };
        script.onerror = () => console.error(`Failed to load script: ${src}`);
        document.body.appendChild(script);
    }

    function cleanupResources(ids = []) {
        ids.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
                console.log(`Removed element: #${id}`);
            }
        });
        // Add specific JS cleanup if needed (e.g., removing event listeners)
        if (currentCleanup && typeof currentCleanup === 'function') {
            console.log("Running specific view cleanup function.");
            currentCleanup();
            currentCleanup = null; // Reset cleanup function
        }
    }

    // --- View Loading Functions ---

    async function loadCliView() {
        try {
            // Fetch HTML partial from the *shell* blueprint route
            const response = await fetch('/view/cli'); // Route defined in shell/routes.py
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const html = await response.text();
            viewContainer.innerHTML = html;

            // Define resources for CLI view
            const cssId = 'cli-css';
            const jsId = 'cli-js';
            const cssPath = '/cli-static/css/terminal.css'; // Path relative to cli blueprint static folder
            const jsPath = '/cli-static/js/terminal.js';   // Path relative to cli blueprint static folder

            // Load CSS and JS, then initialize
            loadCSS(cssPath, cssId);
            // The callback 'initializeTerminalInterface' must be exposed globally by terminal.js
            loadJS(jsPath, jsId, 'initializeTerminalInterface');

            // Set cleanup function for when leaving CLI view
            currentCleanup = () => {
                console.log("Cleaning up CLI view resources...");
                cleanupResources([cssId, jsId]);
                // Add any CLI specific listener removals here if necessary
            };

        } catch (error) {
            console.error("Error loading CLI view:", error);
            viewContainer.innerHTML = `<p class="text-red-500 p-4 text-center self-center">Error loading Developer view: ${error.message}</p>`;
            viewContainer.classList.add('items-center', 'justify-center');
        }
    }

    async function loadRecruiterView() {
        // Placeholder - TODO: Implement in future step
        console.log("Loading Recruiter View (Placeholder)...");
         viewContainer.innerHTML = `<p class="text-center text-xl p-10 self-center">Loading Recruiter Path... (Coming soon!)</p>`;
         viewContainer.classList.add('items-center', 'justify-center');
        currentCleanup = () => { console.log("Cleaning up placeholder Recruiter view"); }; // Basic cleanup
    }

     async function loadVisualView() {
        // Placeholder - TODO: Implement in future step
        console.log("Loading Visual View (Placeholder)...");
        viewContainer.innerHTML = `<p class="text-center text-xl p-10 self-center">Loading Visual Overview... (Coming soon!)</p>`;
        viewContainer.classList.add('items-center', 'justify-center');
        currentCleanup = () => { console.log("Cleaning up placeholder Visual view"); }; // Basic cleanup
    }


    // --- Main Flow Control ---
    function showView(viewName) {
        console.log(`Attempting to show view: ${viewName}`);
        selectorContainer.style.display = 'none';
        viewContainer.innerHTML = ''; // Clear previous content first
        // Reset base classes for the container
        viewContainer.className = 'active'; // Use class for active state styling
        backButton.classList.remove('hidden');
        currentView = viewName;

        // Reset container styles, specific views will add their needs
         viewContainer.classList.remove('items-center', 'justify-center');

        // Call the appropriate loading function
        if (viewName === 'Developer') {
            loadCliView();
        } else if (viewName === 'Recruiter') {
            loadRecruiterView();
        } else if (viewName === 'Visual') {
            loadVisualView();
        } else {
            console.error(`Unknown view name: ${viewName}`);
            viewContainer.innerHTML = `<p class="text-red-500 p-4">Error: Unknown view requested.</p>`;
        }
    }

    function showSelector() {
        console.log("Returning to selector");
        viewContainer.innerHTML = ''; // Clear view content
        viewContainer.classList.add('hidden');
        viewContainer.classList.remove('active'); // Remove active state class
        backButton.classList.add('hidden');
        selectorContainer.style.display = 'block'; // Show selector again

        // Run cleanup for the view we are leaving
        if (currentCleanup && typeof currentCleanup === 'function') {
            currentCleanup();
        } else {
             // Fallback cleanup if specific function wasn't set
             cleanupResources(['cli-css', 'cli-js', 'recruiter-css', 'recruiter-js', 'visual-css', 'visual-js']);
        }

        currentView = null;
    }

    // --- Event Listeners ---
    if (cliOption) cliOption.addEventListener('click', () => showView('Developer'));
    if (recruiterOption) recruiterOption.addEventListener('click', () => showView('Recruiter'));
    if (visualOption) visualOption.addEventListener('click', () => showView('Visual'));
    if (backButton) backButton.addEventListener('click', showSelector);

    console.log("Selector view initialized and ready.");
});