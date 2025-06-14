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
    let isTransitioning = false;

    // --- Helper Functions (loadCSS, loadJS, cleanupResources - Keep as is) ---
    function loadCSS(href, id) { if (document.getElementById(id)) return; const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = href; link.id = id; document.head.appendChild(link); console.log(`CSS loaded: ${href}`); }
    function loadJS(src, id, callbackName) { if (document.getElementById(id)) { if (callbackName && typeof window[callbackName] === 'function') { console.log(`JS already loaded (${src}), calling ${callbackName}()`); window[callbackName](); } else { console.log(`JS already loaded (${src}), no valid callback specified.`); } return; } const script = document.createElement('script'); script.src = src; script.id = id; script.async = false; script.onload = () => { console.log(`JS loaded: ${src}`); if (callbackName && typeof window[callbackName] === 'function') { console.log(`Calling ${callbackName}()`); window[callbackName](); } else if (callbackName) { console.warn(`JS ${src} loaded, but callback ${callbackName} not found or not a function.`); } }; script.onerror = () => console.error(`Failed to load script: ${src}`); document.body.appendChild(script); }
    function cleanupResources(ids = []) { ids.forEach(id => { const element = document.getElementById(id); if (element) { element.remove(); console.log(`Removed element: #${id}`); } }); }


    // --- View Loading Functions (Keep as is) ---
    async function loadCliView() { /* ... As before ... */ try { const response = await fetch('/view/cli'); if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`); const html = await response.text(); viewContainer.innerHTML = html; const cssId = 'cli-css'; const jsId = 'cli-js'; const cssPath = '/cli/static/css/terminal.css'; const jsPath = '/cli/static/js/terminal.js'; const initializerCallback = 'initializeTerminalInterface'; loadCSS(cssPath, cssId); loadJS(jsPath, jsId, initializerCallback); currentCleanup = () => { console.log("Cleaning up CLI view resources..."); cleanupResources([cssId, jsId]); }; } catch (error) { console.error("Error loading CLI view:", error); viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Developer view: ${error.message}</p></div>`; viewContainer.classList.add('items-center', 'justify-center'); } }
    async function loadRecruiterView() { /* ... As before ... */ try { const response = await fetch('/view/recruiter'); if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`); const html = await response.text(); viewContainer.innerHTML = html; const cssId = 'recruiter-css'; const jsId = 'recruiter-js'; const cssPath = '/recruiter/static/css/chat.css'; const jsPath = '/recruiter/static/js/cyoa.js'; const initializerCallback = 'initializeRecruiterView'; const cleanupCallback = 'cleanupRecruiterView'; loadCSS(cssPath, cssId); loadJS(jsPath, jsId, initializerCallback); currentCleanup = () => { console.log("Cleaning up Recruiter view resources..."); if (window[cleanupCallback] && typeof window[cleanupCallback] === 'function') { window[cleanupCallback](); } cleanupResources([cssId, jsId]); }; } catch (error) { console.error("Error loading Recruiter view:", error); viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Recruiter path: ${error.message}</p></div>`; viewContainer.classList.add('items-center', 'justify-center'); } }
    async function loadVisualView() { /* ... As before ... */ try { const response = await fetch('/view/visual'); if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`); const html = await response.text(); viewContainer.innerHTML = html; const cssId = 'visual-css'; const jsId = 'visual-js'; const cssPath = '/visual/static/css/visual.css'; const jsPath = '/visual/static/js/visual.js'; const initializerCallback = 'initializeVisualView'; const cleanupCallback = 'cleanupVisualView'; loadCSS(cssPath, cssId); loadJS(jsPath, jsId, initializerCallback); currentCleanup = () => { console.log("Cleaning up Visual view resources..."); if (window[cleanupCallback] && typeof window[cleanupCallback] === 'function') { window[cleanupCallback](); } cleanupResources([cssId, jsId]); }; } catch (error) { console.error("Error loading Visual view:", error); viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Visual overview: ${error.message}</p></div>`; viewContainer.classList.add('items-center', 'justify-center'); } }


    // --- Main Flow Control (Updated for Transitions & View Class) ---

    /**
     * Hides the selector and loads/shows the specified view with transitions.
     * @param {string} viewName - The name of the view to load ('Developer', 'Recruiter', 'Visual').
     */
    function showView(viewName) {
        if (!viewName || isTransitioning) return;
        isTransitioning = true;
        console.log(`Attempting to show view: ${viewName}`);

        // 1. Start hiding the selector
        selectorContainer.classList.remove('visible-view');
        selectorContainer.classList.add('hidden-view');
        backButton.classList.remove('visible-view');
        backButton.classList.add('hidden-view');

        // 2. After selector fade out delay, load and show the new view
        setTimeout(async () => {
            viewContainer.innerHTML = '';
            viewContainer.className = 'hidden-view'; // Base class, start hidden
            currentView = viewName;

            // Add view-specific class for styling container (e.g., background)
            let viewSpecificClass = '';
            switch (viewName) {
                case 'Developer':
                    viewSpecificClass = 'view-active-cli';
                    await loadCliView();
                    break;
                case 'Recruiter':
                    viewSpecificClass = 'view-active-recruiter';
                    await loadRecruiterView();
                    break;
                case 'Visual':
                     viewSpecificClass = 'view-active-visual';
                    await loadVisualView();
                    break;
                default:
                    console.error(`Unknown view name requested: ${viewName}`);
                    viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error: Unknown view requested.</p></div>`;
                    viewContainer.classList.add('items-center', 'justify-center', 'flex'); // Center error
            }

             // Add the specific class *before* making it visible
             if (viewSpecificClass) {
                 viewContainer.classList.add(viewSpecificClass);
             }

            // Short delay before making view visible allows content to render slightly
            await new Promise(resolve => setTimeout(resolve, 50));

            // 3. Make the view container visible
            viewContainer.classList.remove('hidden-view');
            viewContainer.classList.add('visible-view');
            backButton.classList.remove('hidden-view');
            backButton.classList.add('visible-view');

            isTransitioning = false; // Allow actions again
        }, 400); // Match CSS transition duration
    }

    /**
     * Hides the current view, runs cleanup, and shows the selector again with transitions.
     */
    function showSelector() {
        if (isTransitioning) return;
        isTransitioning = true;
        console.log("Returning to selector");

        // 1. Start hiding the current view
        viewContainer.classList.remove('visible-view');
        viewContainer.classList.add('hidden-view');
        backButton.classList.remove('visible-view');
        backButton.classList.add('hidden-view');

        // 2. Run cleanup after starting fade out
        if (currentCleanup && typeof currentCleanup === 'function') {
            currentCleanup();
        } else {
             console.warn("No specific cleanup function found. Running generic cleanup.");
             cleanupResources(['cli-css', 'cli-js', 'recruiter-css', 'recruiter-js', 'visual-css', 'visual-js']);
        }

         // Remove view-specific class from container *after* starting fade out
         if (currentView) {
             let viewSpecificClass = '';
             if (currentView === 'Developer') viewSpecificClass = 'view-active-cli';
             else if (currentView === 'Recruiter') viewSpecificClass = 'view-active-recruiter';
             else if (currentView === 'Visual') viewSpecificClass = 'view-active-visual';
             if (viewSpecificClass) viewContainer.classList.remove(viewSpecificClass);
         }
         currentView = null;
         currentCleanup = null;

         // 3. After view fade out delay, show the selector
         setTimeout(() => {
            viewContainer.innerHTML = ''; // Clear content after fade out
            selectorContainer.classList.remove('hidden-view');
            selectorContainer.classList.add('visible-view');
            isTransitioning = false; // Allow actions again
         }, 400); // Match CSS transition duration
    }

    // --- Event Listeners ---
    if (cliOption) cliOption.addEventListener('click', () => showView('Developer')); else console.error("#select-cli not found");
    if (recruiterOption) recruiterOption.addEventListener('click', () => showView('Recruiter')); else console.error("#select-recruiter not found");
    if (visualOption) visualOption.addEventListener('click', () => showView('Visual')); else console.error("#select-visual not found");
    if (backButton) backButton.addEventListener('click', showSelector); else console.error("#back-button not found");

    // Set initial state correctly
    selectorContainer.classList.add('visible-view');
    selectorContainer.classList.remove('hidden-view');
    viewContainer.classList.add('hidden-view');
    viewContainer.classList.remove('visible-view');
    backButton.classList.add('hidden-view');
    backButton.classList.remove('visible-view');

    console.log("Selector view initialized with transitions and ready.");
}); // End DOMContentLoaded
