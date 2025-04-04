document.addEventListener('DOMContentLoaded', () => {
    const selectorContainer = document.getElementById('selector-container');
    const viewContainer = document.getElementById('view-container');
    const backButton = document.getElementById('back-button');

    const cliOption = document.getElementById('select-cli');
    const recruiterOption = document.getElementById('select-recruiter');
    const visualOption = document.getElementById('select-visual');

    let currentView = null; // To track which view is active

    function showView(viewName) {
        console.log(`Attempting to show view: ${viewName}`);
        selectorContainer.style.display = 'none'; // Hide selector smoothly if needed later
        viewContainer.innerHTML = ''; // Clear previous content
        viewContainer.classList.remove('hidden');
        viewContainer.classList.add('active'); // Make it cover the screen (uses CSS)
        backButton.classList.remove('hidden');
        currentView = viewName;

        // --- Placeholder Content ---
        // Clear previous content styles if necessary
        viewContainer.className = 'active'; // Reset class list, keep 'active'
        viewContainer.classList.add('p-8', 'flex', 'items-center', 'justify-center'); // Basic styling for placeholder

        const placeholder = document.createElement('div');
        placeholder.className = 'text-center';
        placeholder.innerHTML = `
            <h2 class="text-2xl font-semibold mb-4">Loading ${viewName} View...</h2>
            <p class="text-gray-600">(Content will be loaded dynamically in the next steps)</p>
        `;
        viewContainer.appendChild(placeholder);
        // --- End Placeholder ---


        // TODO: Implement dynamic loading of actual view content (HTML, CSS, JS)
        // Example for future step:
        // if (viewName === 'Developer') { loadCliView(); }
        // else if (viewName === 'Recruiter') { loadRecruiterView(); }
        // else if (viewName === 'Visual') { loadVisualView(); }
    }

    function showSelector() {
        console.log("Returning to selector");
        viewContainer.innerHTML = ''; // Clear content
        viewContainer.classList.add('hidden');
        viewContainer.classList.remove('active');
        backButton.classList.add('hidden');
        selectorContainer.style.display = 'block'; // Show selector
        currentView = null;

        // TODO: Implement cleanup of dynamically loaded resources (CSS, JS listeners) later
        // cleanupDynamicResources();
    }

    // --- Event Listeners ---
    if (cliOption) cliOption.addEventListener('click', () => showView('Developer'));
    if (recruiterOption) recruiterOption.addEventListener('click', () => showView('Recruiter'));
    if (visualOption) visualOption.addEventListener('click', () => showView('Visual'));
    if (backButton) backButton.addEventListener('click', showSelector);

    console.log("Selector view initialized.");
});