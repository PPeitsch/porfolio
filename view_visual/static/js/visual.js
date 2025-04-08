function initializeVisualView() {
    console.log("Attempting to initialize Visual Overview View...");

    const gridContainer = document.getElementById('project-grid');

    if (!gridContainer) {
        console.error("Visual view init failed: #project-grid container not found!");
        return;
    }

    let projectsData = null; // To store fetched project data

    function createProjectCard(project, index) {
        const card = document.createElement('div');
        card.className = 'project-card-visual'; // Base class from CSS
        // Add animation delay based on index
        card.style.animationDelay = `${index * 0.08}s`; // Stagger effect

        const imageSrc = project.image ? `/static/images/projects/${project.image}` : '/static/images/placeholder.png'; // TODO: Need robust image path handling

        let tagsHtml = '';
        if (project.technologies && project.technologies.length > 0) {
            tagsHtml = project.technologies.map(tag =>
                `<span class="tech-tag-visual">${tag}</span>`
            ).join('');
        }

        let linksHtml = '';
        if (project.live_url && project.type === 'webapp') {
            linksHtml += `
                <a href="${project.live_url}" target="_blank" rel="noopener noreferrer" class="project-link-button primary">
                    <i class="fas fa-external-link-alt fa-xs"></i> View Live
                </a>`;
        }
         if (project.github_url) {
             linksHtml += `
                <a href="${project.github_url}" target="_blank" rel="noopener noreferrer" class="project-link-button secondary">
                    <i class="fab fa-github fa-xs"></i> Code
                </a>`;
         }
         // Add other link types (PyPI, Docs) if desired for this view

        card.innerHTML = `
            <img src="${imageSrc}" alt="${project.title || 'Project Image'}" class="project-image">
            <div class="project-content">
                <h3 class="project-title">${project.title || 'Untitled Project'}</h3>
                <p class="project-description">${project.short_desc || 'No description available.'}</p>
                ${tagsHtml ? `<div class="project-tags">${tagsHtml}</div>` : ''}
                ${linksHtml ? `<div class="project-links">${linksHtml}</div>` : ''}
            </div>
        `;
        return card;
    }

    async function fetchAndRenderProjects() {
        console.log("Fetching project data for visual view...");
        try {
            // Fetch simplified project data from the visual blueprint's API
            const response = await fetch('/visual/api/projects'); // API route in visual/routes.py
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            projectsData = await response.json();

            gridContainer.innerHTML = ''; // Clear loading message

            if (!projectsData || projectsData.length === 0) {
                 gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-gray-500">No projects to display.</p>';
                 return;
            }

            projectsData.forEach((project, index) => {
                const card = createProjectCard(project, index);
                gridContainer.appendChild(card);
            });

        } catch (error) {
            console.error("Error fetching or rendering projects:", error);
            gridContainer.innerHTML = `<p class="text-center col-span-full p-10 text-red-500">Could not load projects: ${error.message}</p>`;
        }
    }


    // --- Initial Load ---
    fetchAndRenderProjects();
    console.log("Visual Overview View Initialized.");


    // --- Cleanup Function (if needed) ---
    window.cleanupVisualView = () => {
        console.log("Running cleanup for Visual view...");
        // Remove specific listeners or intervals if added later
        projectsData = null; // Clear data
    };

} // End of initializeVisualView

// Make initializer globally accessible
window.initializeVisualView = initializeVisualView;
window.cleanupVisualView = window.cleanupVisualView || (() => { console.log("Default Visual cleanup"); });
