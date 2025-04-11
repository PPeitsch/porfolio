// unified-portfolio/view_visual/static/js/visual.js
// Step 5.3: Refine card creation, add overlay

function initializeVisualView() {
    console.log("Attempting to initialize Visual Overview View...");
    const gridContainer = document.getElementById('project-grid');
    if (!gridContainer) { /* ... error handling ... */ return; }
    let projectsData = null;

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

        const imageSrc = project.image_url || '/shell-static/images/placeholder.svg';
        const img = document.createElement('img');
        img.src = imageSrc;
        img.alt = `${project.title || 'Project'} Screenshot`;
        img.className = 'project-image';
        img.loading = 'lazy';

        if (imageSrc.toLowerCase().endsWith('.svg')) {
            img.classList.add('svg-image'); // Add class for SVG styling
        }
        imageContainer.appendChild(img);

        // --- Add Image Overlay ---
        const overlay = document.createElement('div');
        overlay.className = 'image-overlay'; // Class from visual.css
        // Add content to overlay (e.g., view link if available)
        if (project.live_url && project.type === 'webapp') {
             const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = 'View Live Project';
             overlay.appendChild(overlayText);

             const overlayLink = document.createElement('a');
             overlayLink.href = project.live_url;
             overlayLink.target = '_blank';
             overlayLink.rel = 'noopener noreferrer';
             overlayLink.className = 'overlay-link';
             overlayLink.innerHTML = '<i class="fas fa-external-link-alt fa-xs"></i> Go';
             overlay.appendChild(overlayLink);
        } else if (project.github_url) {
             // Show GitHub link if no live link
             const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = 'View Source Code';
             overlay.appendChild(overlayText);

             const overlayLink = document.createElement('a');
             overlayLink.href = project.github_url;
             overlayLink.target = '_blank';
             overlayLink.rel = 'noopener noreferrer';
             overlayLink.className = 'overlay-link';
             overlayLink.innerHTML = '<i class="fab fa-github fa-xs"></i> GitHub';
             overlay.appendChild(overlayLink);
        } else {
             // Fallback text if no primary link
              const overlayText = document.createElement('div');
             overlayText.className = 'overlay-text';
             overlayText.textContent = project.title || 'Project'; // Just show title maybe
             overlay.appendChild(overlayText);
        }
        imageContainer.appendChild(overlay); // Add overlay to image container
        // --- End Image Overlay ---

        card.appendChild(imageContainer); // Add image container (with image and overlay) to card

        // --- Content Area (Title, Desc, Tags, Links - Keep as before) ---
        const contentDiv = document.createElement('div');
        contentDiv.className = 'project-content';
        const title = document.createElement('h3');
        title.className = 'project-title';
        title.textContent = project.title || 'Untitled Project';
        contentDiv.appendChild(title);
        const description = document.createElement('p');
        description.className = 'project-description';
        description.textContent = project.short_desc || 'No description available.';
        contentDiv.appendChild(description);
        if (project.technologies && project.technologies.length > 0) { /* ... create tags ... */ const tagsContainer = document.createElement('div'); tagsContainer.className = 'project-tags'; project.technologies.forEach(tag => { const tagSpan = document.createElement('span'); tagSpan.className = 'tech-tag-visual'; tagSpan.textContent = tag; tagsContainer.appendChild(tagSpan); }); contentDiv.appendChild(tagsContainer); }
        const linksContainer = document.createElement('div');
        linksContainer.className = 'project-links';
        let hasLinks = false;
        if (project.live_url && project.type === 'webapp') { /* ... create live link ... */ const link = document.createElement('a'); link.href = project.live_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.className = 'project-link-button primary'; link.innerHTML = '<i class="fas fa-external-link-alt fa-xs"></i> View Live'; linksContainer.appendChild(link); hasLinks = true; }
        if (project.github_url) { /* ... create code link ... */ const link = document.createElement('a'); link.href = project.github_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.className = 'project-link-button secondary'; link.innerHTML = '<i class="fab fa-github fa-xs"></i> Code'; linksContainer.appendChild(link); hasLinks = true; }
        if (project.pypi_url && project.type === 'library') { /* ... create pypi link ... */ const link = document.createElement('a'); link.href = project.pypi_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.className = 'project-link-button secondary'; link.innerHTML = '<i class="fab fa-python fa-xs"></i> PyPI'; linksContainer.appendChild(link); hasLinks = true; }
        if (project.docs_url && project.type === 'library') { /* ... create docs link ... */ const link = document.createElement('a'); link.href = project.docs_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.className = 'project-link-button secondary'; link.innerHTML = '<i class="fas fa-book fa-xs"></i> Docs'; linksContainer.appendChild(link); hasLinks = true; }
        if (hasLinks) { contentDiv.appendChild(linksContainer); }

        card.appendChild(contentDiv);
        return card;
    }

    /**
     * Fetches project data from the API and renders the cards.
     */
    async function fetchAndRenderProjects() { /* ... Keep as before ... */ console.log("Fetching project data for visual view..."); gridContainer.innerHTML = '<div class="text-center col-span-full p-10 text-gray-500 animate-pulse">Loading projects...</div>'; try { const response = await fetch('/visual/api/projects'); if (!response.ok) throw new Error(`HTTP Error: ${response.status}`); projectsData = await response.json(); gridContainer.innerHTML = ''; if (!projectsData || projectsData.length === 0) { gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-gray-500">No projects to display.</p>'; return; } projectsData.forEach((project, index) => { if (project && project.id) { const card = createProjectCard(project, index); gridContainer.appendChild(card); } else { console.warn("Skipping invalid project data item:", project); } }); } catch (error) { console.error("Error fetching or rendering projects:", error); gridContainer.innerHTML = `<p class="text-center col-span-full p-10 text-red-500">Could not load projects: ${error.message}</p>`; } }

    // --- Initial Load ---
    fetchAndRenderProjects();
    console.log("Visual Overview View Initialized.");

    // --- Cleanup Function ---
    window.cleanupVisualView = () => { /* ... Keep as before ... */ console.log("Running cleanup for Visual view..."); projectsData = null; };

} // End of initializeVisualView

window.initializeVisualView = initializeVisualView;
window.cleanupVisualView = window.cleanupVisualView || (() => { console.log("Default Visual cleanup"); });
