function initializeVisualView() {
    console.log("Attempting to initialize Visual Overview View...");

    const gridContainer = document.getElementById('project-grid');

    if (!gridContainer) {
        console.error("Visual view init failed: #project-grid container not found!");
        return;
    }

    let projectsData = null; // Store fetched data if needed later

    /**
     * Creates an HTML project card element.
     * @param {object} project - The project data object.
     * @param {number} index - The index of the project for animation delay.
     * @returns {HTMLElement} - The generated card element.
     */
    function createProjectCard(project, index) {
        const card = document.createElement('div');
        card.className = 'project-card-visual';
        card.style.animationDelay = `${index * 0.08}s`;

        // --- Image Container ---
        const imageContainer = document.createElement('div');
        imageContainer.className = 'image-container'; // Class from visual.css

        const imageSrc = project.image_url || '/shell-static/images/placeholder.svg'; // Fallback defined in Step 5.1.1 correction
        const img = document.createElement('img');
        img.src = imageSrc;
        img.alt = uiText('visual.screenshot_alt', { title: project.title || '' });
        img.className = 'project-image';
        img.loading = 'lazy';

        if (imageSrc.toLowerCase().endsWith('.svg')) {
            img.classList.add('svg-image'); // Add class for SVG styling
        }
        imageContainer.appendChild(img);

        // --- Add Image Overlay ---
        const overlay = document.createElement('div');
        overlay.className = 'image-overlay'; // Class from visual.css
        // Add content to overlay
        if (project.live_url && project.type === 'webapp') {
             const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = uiText('visual.overlay_live');
             overlay.appendChild(overlayText);

             const overlayLink = document.createElement('a');
             overlayLink.href = project.live_url;
             overlayLink.target = '_blank';
             overlayLink.rel = 'noopener noreferrer';
             overlayLink.className = 'overlay-link';
             overlayLink.innerHTML = '<i class="fas fa-external-link-alt fa-xs"></i> ';
             overlayLink.append(uiText('visual.overlay_go'));
             overlay.appendChild(overlayLink);
        } else if (project.github_url) { // Show GitHub if no live link
             const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = uiText('visual.overlay_source');
             overlay.appendChild(overlayText);

             const overlayLink = document.createElement('a');
             overlayLink.href = project.github_url;
             overlayLink.target = '_blank';
             overlayLink.rel = 'noopener noreferrer';
             overlayLink.className = 'overlay-link';
             overlayLink.innerHTML = '<i class="fab fa-github fa-xs"></i> GitHub';
             overlay.appendChild(overlayLink);
        } else { // Fallback text if no primary link
              const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = project.title || 'Project'; // Just show title
             overlay.appendChild(overlayText);
        }
        imageContainer.appendChild(overlay);
        // --- End Image Overlay ---

        card.appendChild(imageContainer); // Add image container to card

        // --- Content Area ---
        const contentDiv = document.createElement('div');
        contentDiv.className = 'project-content';

        // Title
        const title = document.createElement('h3');
        title.className = 'project-title';
        title.textContent = project.title || uiText('visual.untitled');
        contentDiv.appendChild(title);

        // Description
        const description = document.createElement('p');
        description.className = 'project-description';
        description.textContent = project.short_desc || uiText('visual.no_description');
        contentDiv.appendChild(description);

        // Tags (Conditional) - **Restored Logic**
        if (project.technologies && project.technologies.length > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'project-tags'; // Class from visual.css
            project.technologies.forEach(tag => {
                const tagSpan = document.createElement('span');
                tagSpan.className = 'tech-tag-visual'; // Class from visual.css
                tagSpan.textContent = tag;
                tagsContainer.appendChild(tagSpan);
            });
            contentDiv.appendChild(tagsContainer); // Appended before links
        }

        // Links (Conditional) - **Restored Logic**
        const linksContainer = document.createElement('div');
        linksContainer.className = 'project-links'; // Class from visual.css
        let hasLinks = false;

        if (project.live_url && project.type === 'webapp') {
            const link = document.createElement('a');
            link.href = project.live_url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'project-link-button primary'; // Class from visual.css
            link.innerHTML = '<i class="fas fa-external-link-alt fa-xs"></i> ';
            link.append(uiText('visual.link_live'));
            linksContainer.appendChild(link);
            hasLinks = true;
        }
        if (project.github_url) {
             const link = document.createElement('a');
             link.href = project.github_url;
             link.target = '_blank';
             link.rel = 'noopener noreferrer';
             link.className = 'project-link-button secondary'; // Class from visual.css
             link.innerHTML = '<i class="fab fa-github fa-xs"></i> ';
             link.append(uiText('visual.link_code'));
             linksContainer.appendChild(link);
             hasLinks = true;
        }
        if (project.pypi_url && project.type === 'library') {
             const link = document.createElement('a');
             link.href = project.pypi_url;
             link.target = '_blank';
             link.rel = 'noopener noreferrer';
             link.className = 'project-link-button secondary'; // Adjust class if needed
             link.innerHTML = '<i class="fab fa-python fa-xs"></i> PyPI';
             linksContainer.appendChild(link);
             hasLinks = true;
        }
         if (project.docs_url && project.type === 'library') {
             const link = document.createElement('a');
             link.href = project.docs_url;
             link.target = '_blank';
             link.rel = 'noopener noreferrer';
             link.className = 'project-link-button secondary'; // Adjust class if needed
             link.innerHTML = '<i class="fas fa-book fa-xs"></i> Docs';
             linksContainer.appendChild(link);
             hasLinks = true;
        }

        // Only append the links container if there were any links
        if (hasLinks) {
            contentDiv.appendChild(linksContainer);
        }

        card.appendChild(contentDiv); // Add content to card
        return card;
    }

    /**
     * Fetches project data from the API and renders the cards.
     */
    async function fetchAndRenderProjects() {
        console.log("Fetching project data for visual view...");
        // Display loading state
        gridContainer.innerHTML = '<div class="text-center col-span-full p-10 text-gray-500 animate-pulse"></div>';
        gridContainer.firstChild.textContent = uiText('visual.loading');

        try {
            // Fetch simplified project data from the visual blueprint's API
            const response = await fetch('/visual/api/projects'); // API route in visual/routes.py
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            projectsData = await response.json(); // Store fetched data

            gridContainer.innerHTML = ''; // Clear loading message

            if (!projectsData || projectsData.length === 0) {
                 gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-gray-500"></p>';
                 gridContainer.firstChild.textContent = uiText('visual.empty');
                 return;
            }

            // Optional: Sort projects maybe?
            // projectsData.sort((a, b) => a.title.localeCompare(b.title));

            // Create and append cards
            projectsData.forEach((project, index) => {
                if (project && project.id) { // Basic check for valid project data
                    const card = createProjectCard(project, index);
                    gridContainer.appendChild(card);
                } else {
                    console.warn("Skipping invalid project data item:", project);
                }
            });

        } catch (error) {
            console.error("Error fetching or rendering projects:", error);
            gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-red-500"></p>';
            gridContainer.firstChild.textContent = uiText('visual.load_error', { error: error.message });
        }
    }

    // --- Initial Load ---
    fetchAndRenderProjects(); // Fetch data and build the grid when the view initializes
    console.log("Visual Overview View Initialized.");

    // --- Cleanup Function (if needed) ---
    window.cleanupVisualView = () => {
        console.log("Running cleanup for Visual view...");
        // No complex listeners added yet, just clear data reference
        projectsData = null;
    };

} // End of initializeVisualView

// Make initializer globally accessible for selector.js
window.initializeVisualView = initializeVisualView;
// Define cleanup function globally
window.cleanupVisualView = window.cleanupVisualView || (() => { console.log("Default Visual cleanup"); });
