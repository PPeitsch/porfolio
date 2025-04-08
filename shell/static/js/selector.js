// Add Visual View loading
document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Elements ---
    const selectorContainer = document.getElementById('selector-container');
    const viewContainer = document.getElementById('view-container');
    const backButton = document.getElementById('back-button');

    const cliOption = document.getElementById('select-cli');
    const recruiterOption = document.getElementById('select-recruiter');
    const visualOption = document.getElementById('select-visual');

    // --- State Variables ---
    let currentView = null;
    let currentCleanup = null;

    // --- Helper Functions (loadCSS, loadJS, cleanupResources - Keep as is) ---
    function loadCSS(href, id) { /* ... */ if (document.getElementById(id)) return; const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = href; link.id = id; document.head.appendChild(link); console.log(`CSS loaded: ${href}`); }
    function loadJS(src, id, callbackName) { /* ... */ if (document.getElementById(id)) { if (callbackName && typeof window[callbackName] === 'function') { console.log(`JS already loaded (${src}), calling ${callbackName}()`); window[callbackName](); } else { console.log(`JS already loaded (${src}), no valid callback specified.`); } return; } const script = document.createElement('script'); script.src = src; script.id = id; script.async = false; script.onload = () => { console.log(`JS loaded: ${src}`); if (callbackName && typeof window[callbackName] === 'function') { console.log(`Calling ${callbackName}()`); window[callbackName](); } else if (callbackName) { console.warn(`JS ${src} loaded, but callback ${callbackName} not found or not a function.`); } }; script.onerror = () => console.error(`Failed to load script: ${src}`); document.body.appendChild(script); }
    function cleanupResources(ids = []) { /* ... */ ids.forEach(id => { const element = document.getElementById(id); if (element) { element.remove(); console.log(`Removed element: #${id}`); } }); }


    // --- View Loading Functions ---
    async function loadCliView() { /* ... Keep as is ... */ try { const response = await fetch('/view/cli'); if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`); const html = await response.text(); viewContainer.innerHTML = html; const cssId = 'cli-css'; const jsId = 'cli-js'; const cssPath = '/cli/static/css/terminal.css'; const jsPath = '/cli/static/js/terminal.js'; const initializerCallback = 'initializeTerminalInterface'; loadCSS(cssPath, cssId); loadJS(jsPath, jsId, initializerCallback); currentCleanup = () => { console.log("Cleaning up CLI view resources..."); cleanupResources([cssId, jsId]); }; } catch (error) { console.error("Error loading CLI view:", error); viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Developer view: ${error.message}</p></div>`; viewContainer.classList.add('items-center', 'justify-center'); } }
    async function loadRecruiterView() { /* ... Keep as is ... */ try { const response = await fetch('/view/recruiter'); if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`); const html = await response.text(); viewContainer.innerHTML = html; const cssId = 'recruiter-css'; const jsId = 'recruiter-js'; const cssPath = '/recruiter/static/css/cyoa.css'; const jsPath = '/recruiter/static/js/cyoa.js'; const initializerCallback = 'initializeRecruiterView'; const cleanupCallback = 'cleanupRecruiterView'; loadCSS(cssPath, cssId); loadJS(jsPath, jsId, initializerCallback); currentCleanup = () => { console.log("Cleaning up Recruiter view resources..."); if (window[cleanupCallback] && typeof window[cleanupCallback] === 'function') { window[cleanupCallback](); } cleanupResources([cssId, jsId]); }; } catch (error) { console.error("Error loading Recruiter view:", error); viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Recruiter path: ${error.message}</p></div>`; viewContainer.classList.add('items-center', 'justify-center'); } }

    /**
     * Loads and initializes the Visual Overview view.
     */
     async function loadVisualView() {
        try {
            // Fetch HTML partial
            const response = await fetch('/view/visual'); // Route defined in shell/routes.py
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const html = await response.text();
            viewContainer.innerHTML = html;

            // Define resources
            const cssId = 'visual-css';
            const jsId = 'visual-js';
            const cssPath = '/visual/static/css/visual.css'; // Use blueprint static path
            const jsPath = '/visual/static/js/visual.js';
            const initializerCallback = 'initializeVisualView'; // Function inside visual.js
            const cleanupCallback = 'cleanupVisualView'; // Optional cleanup

            // Load resources and initialize
            loadCSS(cssPath, cssId);
            loadJS(jsPath, jsId, initializerCallback);

            // Set cleanup
            currentCleanup = () => {
                console.log("Cleaning up Visual view resources...");
                 if (window[cleanupCallback] && typeof window[cleanupCallback] === 'function') {
                     window[cleanupCallback]();
                 }
                cleanupResources([cssId, jsId]);
            };

        } catch (error) {
             console.error("Error loading Visual view:", error);
             viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Visual overview: ${error.message}</p></div>`;
             viewContainer.classList.add('items-center', 'justify-center');
        }
    }


    // --- Main Flow Control ---
    function showView(viewName) {
        if (!viewName) return;
        console.log(`Attempting to show view: ${viewName}`);

        selectorContainer.style.display = 'none';
        viewContainer.innerHTML = '';
        viewContainer.className = 'active'; // Base class, ensures it's displayed
        backButton.classList.remove('hidden');
        currentView = viewName;

        // Reset flex alignment potentially set by placeholders or prior views
        viewContainer.classList.remove('items-center', 'justify-center', 'flex'); // Remove flexbox alignment helpers

        // Call the appropriate loading function based on the view name
        switch (viewName) {
            case 'Developer':
                loadCliView();
                break;
            case 'Recruiter':
                loadRecruiterView();
                break;
            case 'Visual':
                loadVisualView(); // <-- Call new function
                break;
            default:
                console.error(`Unknown view name requested: ${viewName}`);
                viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error: Unknown view requested.</p></div>`;
                viewContainer.classList.add('items-center', 'justify-center', 'flex'); // Re-add for error centering
        }
    }

    function showSelector() { /* ... Keep existing logic ... */ console.log("Returning to selector"); if (currentCleanup && typeof currentCleanup === 'function') { currentCleanup(); } else { console.warn("No specific cleanup function found for current view. Running generic cleanup."); cleanupResources(['cli-css', 'cli-js', 'recruiter-css', 'recruiter-js', 'visual-css', 'visual-js']); } viewContainer.innerHTML = ''; viewContainer.classList.add('hidden'); viewContainer.classList.remove('active'); backButton.classList.add('hidden'); selectorContainer.style.display = 'block'; currentView = null; currentCleanup = null; }

    // --- Event Listeners ---
    if (cliOption) cliOption.addEventListener('click', () => showView('Developer')); else console.error("CLI option element not found");
    if (recruiterOption) recruiterOption.addEventListener('click', () => showView('Recruiter')); else console.error("Recruiter option element not found");
    if (visualOption) visualOption.addEventListener('click', () => showView('Visual')); else console.error("Visual option element not found"); // <-- Add listener
    if (backButton) backButton.addEventListener('click', showSelector); else console.error("Back button element not found");

    console.log("Selector view initialized and ready.");
}); // End DOMContentLoaded; // End DOMContentLoaded
