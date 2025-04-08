// unified-portfolio/view_visual/static/js/visual.js

function initializeVisualView() {
    console.log("Attempting to initialize Visual Overview View...");

    const gridContainer = document.getElementById('project-grid');
    // Optional: Get other elements if needed, e.g., skills container
    // const skillsContainer = document.getElementById('visual-skills');

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
        // Apply base classes and animation class
        card.className = 'project-card-visual'; // Base class includes animation trigger
        // Stagger the animation delay
        card.style.animationDelay = `${index * 0.08}s`;

        // --- Image ---
        // Use the image_url provided by the API
        const imageSrc = project.image_url || '/shell-static/images/placeholder.svg'; // Fallback
        const img = document.createElement('img');
        img.src = imageSrc;
        img.alt = `${project.title || 'Project'} Screenshot`;
        img.className = 'project-image'; // Class from visual.css
        img.loading = 'lazy'; // Improve performance
        card.appendChild(img);

        // --- Content Area ---
        const contentDiv = document.createElement('div');
        contentDiv.className = 'project-content'; // Class from visual.css

        // Title
        const title = document.createElement('h3');
        title.className = 'project-title'; // Class from visual.css
        title.textContent = project.title || 'Untitled Project';
        contentDiv.appendChild(title);

        // Description
        const description = document.createElement('p');
        description.className = 'project-description'; // Class from visual.css
        description.textContent = project.short_desc || 'No description available.';
        contentDiv.appendChild(description);

        // Tags (Conditional)
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

        // Links (Conditional)
        const linksContainer = document.createElement('div');
        linksContainer.className = 'project-links'; // Class from visual.css
        let hasLinks = false;

        if (project.live_url && project.type === 'webapp') {
            const link = document.createElement('a');
            link.href = project.live_url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'project-link-button primary'; // Class from visual.css
            link.innerHTML = '<i class="fas fa-external-link-alt fa-xs"></i> View Live';
            linksContainer.appendChild(link);
            hasLinks = true;
        }
        if (project.github_url) {
             const link = document.createElement('a');
             link.href = project.github_url;
             link.target = '_blank';
             link.rel = 'noopener noreferrer';
             link.className = 'project-link-button secondary'; // Class from visual.css
             link.innerHTML = '<i class="fab fa-github fa-xs"></i> Code';
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
        gridContainer.innerHTML = '<div class="text-center col-span-full p-10 text-gray-500 animate-pulse">Loading projects...</div>';

        try {
            // Fetch simplified project data from the visual blueprint's API
            const response = await fetch('/visual/api/projects'); // API route in visual/routes.py
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            projectsData = await response.json(); // Store fetched data

            gridContainer.innerHTML = ''; // Clear loading message

            if (!projectsData || projectsData.length === 0) {
                 gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-gray-500">No projects to display.</p>';
                 return;
            }

            // Sort projects maybe? (Optional)
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
            gridContainer.innerHTML = `<p class="text-center col-span-full p-10 text-red-500">Could not load projects: ${error.message}</p>`;
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
