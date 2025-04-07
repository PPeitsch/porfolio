document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Elements ---
    const selectorContainer = document.getElementById('selector-container');
    const viewContainer = document.getElementById('view-container');
    const backButton = document.getElementById('back-button');

    const cliOption = document.getElementById('select-cli');
    const recruiterOption = document.getElementById('select-recruiter');
    const visualOption = document.getElementById('select-visual');

    // --- State Variables ---
    let currentView = null; // Tracks the currently displayed view ('Developer', 'Recruiter', 'Visual')
    let currentCleanup = null; // Holds the specific cleanup function for the current view

    // --- Helper Functions for Resource Management ---

    /**
     * Dynamically loads a CSS file into the document head.
     * Avoids loading the same file multiple times.
     * @param {string} href - The URL of the CSS file.
     * @param {string} id - A unique ID for the link element.
     */
    function loadCSS(href, id) {
        if (document.getElementById(id)) {
            console.log(`CSS already loaded: ${href}`);
            return; // Already loaded
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.id = id;
        document.head.appendChild(link);
        console.log(`CSS loaded: ${href}`);
    }

    /**
     * Dynamically loads a JavaScript file into the document body.
     * Avoids loading the same file multiple times.
     * Calls an optional callback function once the script is loaded.
     * @param {string} src - The URL of the JS file.
     * @param {string} id - A unique ID for the script element.
     * @param {string} [callbackName] - Optional name of a global function to call after load.
     */
    function loadJS(src, id, callbackName) {
        if (document.getElementById(id)) {
            // If script tag exists, assume script loaded, try calling callback if provided
            if (callbackName && typeof window[callbackName] === 'function') {
                 console.log(`JS already loaded (${src}), calling ${callbackName}()`);
                 window[callbackName]();
            } else {
                  console.log(`JS already loaded (${src}), no valid callback specified.`);
            }
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.id = id;
        script.async = false; // Load and execute script sequentially relative to other dynamic scripts if needed
        script.onload = () => {
            console.log(`JS loaded: ${src}`);
            // Check if the callback function exists globally *after* loading
            if (callbackName && typeof window[callbackName] === 'function') {
                console.log(`Calling ${callbackName}()`);
                window[callbackName](); // Call the initializer function
            } else if (callbackName) {
                console.warn(`JS ${src} loaded, but callback ${callbackName} not found or not a function.`);
            }
        };
        script.onerror = () => console.error(`Failed to load script: ${src}`);
        document.body.appendChild(script);
    }

    /**
     * Removes dynamically loaded CSS and JS elements by their IDs.
     * @param {string[]} ids - An array of element IDs to remove.
     */
    function cleanupResources(ids = []) {
        ids.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
                console.log(`Removed element: #${id}`);
            }
        });
    }

    // --- View Loading Functions ---

    /**
     * Loads and initializes the Developer (CLI) view.
     */
    async function loadCliView() {
        try {
            // Fetch HTML partial from the shell route /view/cli
            const response = await fetch('/view/cli');
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const html = await response.text();
            viewContainer.innerHTML = html; // Inject the HTML

            // Define resources specific to the CLI view
            const cssId = 'cli-css';
            const jsId = 'cli-js';
            // Use the *new* explicit static file route path
            const cssPath = '/cli/static/css/terminal.css';
            const jsPath = '/cli/static/js/terminal.js';
            const initializerCallback = 'initializeTerminalInterface'; // Function inside terminal.js

            // Load resources and initialize via callback
            loadCSS(cssPath, cssId);
            loadJS(jsPath, jsId, initializerCallback);

            // Set the specific cleanup function for this view
            currentCleanup = () => {
                console.log("Cleaning up CLI view resources...");
                // Add any CLI specific listener removals or cleanup here if needed in future
                cleanupResources([cssId, jsId]); // Remove CSS and JS tags
                // Remove the global initializer if it causes conflicts (optional)
                // delete window[initializerCallback];
            };

        } catch (error) {
            console.error("Error loading CLI view:", error);
            // Display error within the view container
            viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Developer view: ${error.message}</p></div>`;
            viewContainer.classList.add('items-center', 'justify-center'); // Center error
        }
    }

    /**
     * Loads and initializes the Recruiter (CYOA) view.
     */
    async function loadRecruiterView() {
         try {
            // Fetch HTML partial from the shell route /view/recruiter
            const response = await fetch('/view/recruiter');
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const html = await response.text();
            viewContainer.innerHTML = html;

            // Define resources
            const cssId = 'recruiter-css';
            const jsId = 'recruiter-js';
            // Use the *new* explicit static file route path
            const cssPath = '/recruiter/static/css/cyoa.css';
            const jsPath = '/recruiter/static/js/cyoa.js';
            const initializerCallback = 'initializeRecruiterView'; // Function inside cyoa.js
            const cleanupCallback = 'cleanupRecruiterView'; // Optional cleanup function inside cyoa.js

            // Load resources and initialize
            loadCSS(cssPath, cssId);
            loadJS(jsPath, jsId, initializerCallback);

            // Set the specific cleanup function
            currentCleanup = () => {
                console.log("Cleaning up Recruiter view resources...");
                 // Call the specific cleanup function from the view's JS if it exists
                if (window[cleanupCallback] && typeof window[cleanupCallback] === 'function') {
                     window[cleanupCallback]();
                     // Optional: delete window[cleanupCallback];
                }
                cleanupResources([cssId, jsId]); // Remove CSS and JS tags
                // Optional: delete window[initializerCallback];
            };

        } catch (error) {
             console.error("Error loading Recruiter view:", error);
             viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Recruiter path: ${error.message}</p></div>`;
             viewContainer.classList.add('items-center', 'justify-center');
        }
    }

    /**
     * Placeholder function for loading the Visual view.
     */
     async function loadVisualView() {
        // Placeholder - TODO: Implement in Phase 4
        console.log("Loading Visual View (Placeholder)...");
        viewContainer.innerHTML = `<div class="p-8 text-center self-center"><h2 class="text-2xl font-semibold mb-4">Loading Visual Overview...</h2><p class="text-gray-600">(Coming soon!)</p></div>`;
        viewContainer.classList.add('items-center', 'justify-center');
        // Basic cleanup for placeholder
        currentCleanup = () => { console.log("Cleaning up placeholder Visual view"); };
    }


    // --- Main Flow Control ---

    /**
     * Hides the selector and loads the specified view.
     * @param {string} viewName - The name of the view to load ('Developer', 'Recruiter', 'Visual').
     */
    function showView(viewName) {
        if (!viewName) return;
        console.log(`Attempting to show view: ${viewName}`);

        // Hide selector and prepare container
        selectorContainer.style.display = 'none';
        viewContainer.innerHTML = ''; // Clear previous content
        viewContainer.className = 'active'; // Base class for active view (used for CSS targeting/styling)
        backButton.classList.remove('hidden'); // Show back button
        currentView = viewName;

        // Reset common container styles, specific views will add their needs
        viewContainer.classList.remove('items-center', 'justify-center');

        // Call the appropriate loading function based on the view name
        switch (viewName) {
            case 'Developer':
                loadCliView();
                break;
            case 'Recruiter':
                loadRecruiterView();
                break;
            case 'Visual':
                loadVisualView();
                break;
            default:
                console.error(`Unknown view name requested: ${viewName}`);
                viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error: Unknown view requested.</p></div>`;
                viewContainer.classList.add('items-center', 'justify-center'); // Center error
        }
    }

    /**
     * Hides the current view, runs cleanup, and shows the selector again.
     */
    function showSelector() {
        console.log("Returning to selector");

        // Run cleanup for the view we are leaving *before* clearing HTML
        if (currentCleanup && typeof currentCleanup === 'function') {
            currentCleanup();
        } else {
             // Fallback cleanup if specific function wasn't set (might be too aggressive)
             console.warn("No specific cleanup function found for current view. Running generic cleanup.");
             cleanupResources(['cli-css', 'cli-js', 'recruiter-css', 'recruiter-js', 'visual-css', 'visual-js']);
        }

        // Clear and hide view container
        viewContainer.innerHTML = '';
        viewContainer.classList.add('hidden');
        viewContainer.classList.remove('active'); // Remove active state class
        backButton.classList.add('hidden');

        // Show selector
        selectorContainer.style.display = 'block'; // Or 'flex' depending on its layout needs

        // Reset state
        currentView = null;
        currentCleanup = null;
    }

    // --- Event Listeners ---
    if (cliOption) {
        cliOption.addEventListener('click', () => showView('Developer'));
    } else {
        console.error("CLI option element (#select-cli) not found");
    }

    if (recruiterOption) {
        recruiterOption.addEventListener('click', () => showView('Recruiter'));
    } else {
        console.error("Recruiter option element (#select-recruiter) not found");
    }

    if (visualOption) {
        visualOption.addEventListener('click', () => showView('Visual'));
    } else {
        console.error("Visual option element (#select-visual) not found");
    }

    if (backButton) {
        backButton.addEventListener('click', showSelector);
    } else {
        console.error("Back button element (#back-button) not found");
    }

    console.log("Selector view initialized and ready.");
}); // End DOMContentLoaded
