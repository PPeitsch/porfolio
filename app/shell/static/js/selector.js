document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Elements ---
    const selectorContainer = document.getElementById('selector-container');
    const viewContainer = document.getElementById('view-container');
    const viewDock = document.getElementById('view-dock');

    const cliOption = document.getElementById('select-cli');
    const recruiterOption = document.getElementById('select-recruiter');
    const visualOption = document.getElementById('select-visual');

    // --- State Variables ---
    let currentView = null;
    let currentCleanup = null;
    let isTransitioning = false;

    // --- Helper Functions ---
    function loadCSS(href, id) {
        if (document.getElementById(id)) return;
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.id = id;
        document.head.appendChild(link);
        console.log(`CSS loaded: ${href}`);
    }

    function loadJS(src, id, callback) {
        if (document.getElementById(id)) {
            if (callback && typeof callback === 'function') {
                console.log(`JS already loaded (${src}), calling callback...`);
                callback();
            } else if (callback) {
                console.log(`JS already loaded (${src}), but no valid callback specified.`);
            }
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.id = id;
        script.async = false;
        script.onload = () => {
            console.log(`JS loaded: ${src}`);
            if (callback && typeof callback === 'function') {
                callback();
            } else {
                console.warn(`JS ${src} loaded, but callback is not a function.`);
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
    }

    // --- Dock Management ---
    function updateDock(activeView) {
        if (!viewDock) return;
        const dockItems = viewDock.querySelectorAll('.dock-item');
        dockItems.forEach(item => {
            if (item.dataset.view === activeView) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // --- View Loading Functions ---
    async function loadCliView() {
        try {
            const response = await fetch(_app_urls.view_cli);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            viewContainer.innerHTML = await response.text();

            const themesCssId = 'cli-themes-css';
            const viewSpecificCssId = 'cli-view-css';
            const viewSpecificJsId = 'cli-view-js';
            const sharedWindowCssId = 'shared-window-css';
            const sharedWindowJsId = 'shared-window-js';

            loadCSS(_app_urls.shared_window_css, sharedWindowCssId);
            loadCSS(_app_urls.cli_css, viewSpecificCssId);
            loadCSS(_app_urls.cli_themes_css, themesCssId); // Load the new themes css
            loadJS(_app_urls.shared_window_js, sharedWindowJsId, () => {
                loadJS(_app_urls.cli_js, viewSpecificJsId, () => {
                    window.initializeCliView({onClose: showSelector});
                });
            });

            currentCleanup = () => {
                console.log("Cleaning up CLI view resources...");
                cleanupResources([viewSpecificCssId, viewSpecificJsId, sharedWindowCssId, sharedWindowJsId, themesCssId]);
            };
        } catch (error) {
            console.error("Error loading CLI view:", error);
            viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Developer view: ${error.message}</p></div>`;
            viewContainer.classList.add('items-center', 'justify-center');
        }
    }

    async function loadRecruiterView() {
        try {
            const response = await fetch(_app_urls.view_recruiter);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            viewContainer.innerHTML = await response.text();

            const viewSpecificCssId = 'recruiter-view-css';
            const viewSpecificJsId = 'recruiter-view-js';
            const sharedWindowCssId = 'shared-window-css';
            const sharedWindowJsId = 'shared-window-js';

            loadCSS(_app_urls.shared_window_css, sharedWindowCssId);
            loadCSS(_app_urls.recruiter_css, viewSpecificCssId);
            loadJS(_app_urls.shared_window_js, sharedWindowJsId, () => {
                loadJS(_app_urls.recruiter_js, viewSpecificJsId, () => {
                    window.initializeRecruiterView({onClose: showSelector});
                });
            });

            currentCleanup = () => {
                console.log("Cleaning up Recruiter view resources...");
                if (window.cleanupRecruiterView && typeof window.cleanupRecruiterView === 'function') {
                    window.cleanupRecruiterView();
                }
                cleanupResources([viewSpecificCssId, viewSpecificJsId, sharedWindowCssId, sharedWindowJsId]);
            };
        } catch (error) {
            console.error("Error loading Recruiter view:", error);
            viewContainer.innerHTML = `<div class="p-8 text-center self-center"><p class="text-red-500">Error loading Recruiter path: ${error.message}</p></div>`;
            viewContainer.classList.add('items-center', 'justify-center');
        }
    }

    async function loadVisualView() {
        try {
            const response = await fetch(_app_urls.view_visual);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            viewContainer.innerHTML = await response.text();

            const cssId = 'visual-css';
            const jsId = 'visual-js';

            loadCSS(_app_urls.visual_css, cssId);
            loadJS(_app_urls.visual_js, jsId, () => {
                if (window.initializeVisualView) window.initializeVisualView();
            });

            currentCleanup = () => {
                console.log("Cleaning up Visual view resources...");
                if (window.cleanupVisualView && typeof window.cleanupVisualView === 'function') {
                    window.cleanupVisualView();
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
    async function showView(viewName) {
        if (!viewName || (isTransitioning && currentView !== null) || viewName === currentView) return;
        isTransitioning = true;
        console.log(`Transitioning to view: ${viewName}`);

        // --- Run cleanup for the old view if it exists ---
        if (currentView !== null) {
            viewContainer.classList.remove('visible-view');
            viewContainer.classList.add('hidden-view');
            if (currentCleanup) {
                currentCleanup();
                currentCleanup = null;
            }
        } else {
            selectorContainer.classList.remove('visible-view');
            selectorContainer.classList.add('hidden-view');
        }

        // --- Show dock and update its active state ---
        viewDock.classList.add('visible');
        updateDock(viewName);

        // --- Wait for fade-out, then load new content ---
        await new Promise(resolve => setTimeout(resolve, 400));

        viewContainer.innerHTML = '';
        viewContainer.className = 'hidden-view';
        currentView = viewName;

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
                viewContainer.classList.add('items-center', 'justify-center', 'flex');
        }

        if (viewSpecificClass) {
            viewContainer.classList.add(viewSpecificClass);
        }

        await new Promise(resolve => setTimeout(resolve, 50));
        viewContainer.classList.remove('hidden-view');
        viewContainer.classList.add('visible-view');

        isTransitioning = false;
    }

    function showSelector() {
        if (isTransitioning) return;
        isTransitioning = true;
        console.log("Returning to selector");

        viewContainer.classList.remove('visible-view');
        viewContainer.classList.add('hidden-view');
        viewDock.classList.remove('visible'); // Hide the dock

        if (currentCleanup) {
            currentCleanup();
            currentCleanup = null;
        }

        if (currentView) {
            let viewSpecificClass = '';
            if (currentView === 'Developer') viewSpecificClass = 'view-active-cli';
            else if (currentView === 'Recruiter') viewSpecificClass = 'view-active-recruiter';
            else if (currentView === 'Visual') viewSpecificClass = 'view-active-visual';
            if (viewSpecificClass) viewContainer.classList.remove(viewSpecificClass);
        }
        currentView = null;

        setTimeout(() => {
            viewContainer.innerHTML = '';
            selectorContainer.classList.remove('hidden-view');
            selectorContainer.classList.add('visible-view');
            isTransitioning = false;
        }, 400);
    }

    // --- Event Listeners ---
    if (cliOption) cliOption.addEventListener('click', () => showView('Developer'));
    if (recruiterOption) recruiterOption.addEventListener('click', () => showView('Recruiter'));
    if (visualOption) visualOption.addEventListener('click', () => showView('Visual'));

    // --- Dock Event Listeners ---
    if (viewDock) {
        viewDock.addEventListener('click', (event) => {
            const dockItem = event.target.closest('.dock-item');
            if (dockItem) {
                const viewName = dockItem.dataset.view;
                if (viewName === 'Home') {
                    showSelector();
                } else {
                    showView(viewName);
                }
            }
        });
    }

    // --- Initial State ---
    selectorContainer.classList.add('visible-view');
    selectorContainer.classList.remove('hidden-view');
    viewContainer.classList.add('hidden-view');
    viewContainer.classList.remove('visible-view');

    console.log("Selector view initialized with transitions and ready.");
});
