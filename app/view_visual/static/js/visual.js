function initializeVisualView() {
    console.log("Attempting to initialize Visual Overview View...");

    const gridContainer = document.getElementById('project-grid');

    if (!gridContainer) {
        console.error("Visual view init failed: #project-grid container not found!");
        return;
    }

    let projectsData = null; // Store fetched data if needed later

    // Stroke icons in currentColor, so they follow the theme.
    const svgIcon = (paths) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
    const ICONS = {
        site: svgIcon('<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'),
        github: svgIcon('<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>'),
        pypi: svgIcon('<path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.29 7 12 12l8.71-5"/><path d="M12 22V12"/>'),
        docs: svgIcon('<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>'),
        webapp: svgIcon('<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>'),
        library: svgIcon('<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 7.7 4.73a2 2 0 0 0 2 0L20.7 7"/>'),
        'data-analysis': svgIcon('<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="m19 9-5 5-4-4-3 3"/>'),
        api: svgIcon('<path d="M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1"/><path d="M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"/>'),
        mobile: svgIcon('<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>'),
        repo: svgIcon('<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>'),
        tool: svgIcon('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
    };
    const MAX_TAGS = 4;
    const PLACEHOLDER_PROMPT = 'guest@portfolio:~ $';

    function element(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text !== undefined) el.textContent = text;
        return el;
    }

    // What the placeholder's terminal "runs": the same link the card opens.
    function placeholderCommand(project) {
        if (project.type === 'library') return `pip install ${project.id}`;
        const strip = (url) => url.replace(/^https?:\/\//, '');
        if (project.type === 'webapp' && project.live_url) return `open ${strip(project.live_url)}`;
        if (project.github_url) return `git clone ${strip(project.github_url)}`;
        return `cd ${project.id}`;
    }

    /**
     * A window like the CLI's, shown when the project has no screenshot.
     * @param {object} project - The project data object.
     * @returns {HTMLElement}
     */
    function createPlaceholder(project) {
        const placeholder = element('div', 'project-placeholder');
        const win = element('div', 'placeholder-window');

        const bar = element('div', 'placeholder-bar');
        const title = element('div', 'placeholder-title');
        title.innerHTML = '<i class="fas fa-terminal"></i>';
        title.appendChild(element('span', '', project.id));
        const controls = element('div', 'placeholder-controls');
        controls.innerHTML = '<i class="minimize"></i><i class="maximize"></i><i class="close"></i>';
        bar.append(title, controls);

        const terminal = element('div', 'placeholder-terminal');
        const commandLine = element('div');
        commandLine.append(element('span', 'prompt', PLACEHOLDER_PROMPT), placeholderCommand(project));
        const comment = element('div', 'comment', `# ${uiText('visual.no_screenshot')}`);
        const cursorLine = element('div');
        cursorLine.append(element('span', 'prompt', PLACEHOLDER_PROMPT), element('span', 'placeholder-cursor'));
        terminal.append(commandLine, comment, cursorLine);

        win.append(bar, terminal);
        placeholder.appendChild(win);
        return placeholder;
    }

    function createLinkButton(url, icon, tip, label) {
        const link = element('a', 'project-link-button');
        link.href = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.dataset.tip = tip;
        link.setAttribute('aria-label', label);
        link.innerHTML = icon;
        return link;
    }

    /**
     * Creates an HTML project card element.
     * @param {object} project - The project data object.
     * @param {number} index - The index of the project for animation delay.
     * @returns {HTMLElement} - The generated card element.
     */
    function createProjectCard(project, index) {
        const card = element('article', 'project-card-visual');
        card.style.animationDelay = `${index * 0.04}s`;
        const title = project.title || uiText('visual.untitled');
        // The live site only for web apps; the rest open their code.
        const liveUrl = project.type === 'webapp' ? project.live_url : null;
        const mainUrl = liveUrl || project.github_url || project.docs_url || project.pypi_url;

        // --- Image, or the placeholder window ---
        const media = element(mainUrl ? 'a' : 'div', 'project-media');
        if (mainUrl) {
            media.href = mainUrl;
            media.target = '_blank';
            media.rel = 'noopener noreferrer';
            media.tabIndex = -1; // The buttons below are the keyboard path
            media.setAttribute('aria-hidden', 'true');
        }
        if (project.image_url) {
            const img = element('img');
            img.src = project.image_url;
            img.alt = uiText('visual.screenshot_alt', { title });
            img.loading = 'lazy';
            img.addEventListener('error', () => img.replaceWith(createPlaceholder(project)), { once: true });
            media.appendChild(img);
        } else {
            media.appendChild(createPlaceholder(project));
        }
        card.appendChild(media);

        const body = element('div', 'project-body');

        // --- Title and type ---
        const head = element('div', 'project-head');
        head.appendChild(element('h3', 'project-title', title));
        if (project.type_label) {
            const kind = element('span', 'project-kind');
            kind.innerHTML = ICONS[project.type] || ICONS.repo;
            kind.append(project.type_label);
            head.appendChild(kind);
        }
        body.appendChild(head);

        body.appendChild(element('p', 'project-description', project.short_desc || uiText('visual.no_description')));

        // --- Footer: tags and links ---
        const foot = element('div', 'project-foot');
        const tags = element('div', 'project-tags');
        const technologies = project.technologies || [];
        technologies.slice(0, MAX_TAGS).forEach(tech => tags.appendChild(element('span', 'tech-tag-visual', tech)));
        const rest = technologies.slice(MAX_TAGS);
        if (rest.length) {
            const more = element('span', 'tech-tag-visual more', `+${rest.length}`);
            more.dataset.tip = rest.join(', ');
            more.tabIndex = 0;
            tags.appendChild(more);
        }
        foot.appendChild(tags);

        const links = element('div', 'project-links');
        if (liveUrl) {
            links.appendChild(createLinkButton(liveUrl, ICONS.site, uiText('visual.link_site'),
                uiText('visual.link_site_label', { title })));
        }
        if (project.github_url) {
            links.appendChild(createLinkButton(project.github_url, ICONS.github, uiText('visual.link_code'),
                uiText('visual.link_code_label', { title })));
        }
        if (project.type === 'library' && project.pypi_url) {
            links.appendChild(createLinkButton(project.pypi_url, ICONS.pypi, uiText('visual.link_pypi'),
                uiText('visual.link_pypi_label', { title })));
        }
        if (project.type === 'library' && project.docs_url) {
            links.appendChild(createLinkButton(project.docs_url, ICONS.docs, uiText('visual.link_docs'),
                uiText('visual.link_docs_label', { title })));
        }
        if (links.children.length) foot.appendChild(links);
        if (tags.children.length || links.children.length) body.appendChild(foot);

        card.appendChild(body);
        return card;
    }

    /**
     * Fetches project data from the API and renders the cards.
     */
    async function fetchAndRenderProjects() {
        console.log("Fetching project data for visual view...");
        // Display loading state
        gridContainer.innerHTML = '<div class="text-center col-span-full p-10 text-muted animate-pulse"></div>';
        gridContainer.firstChild.textContent = uiText('visual.loading');

        try {
            // Fetch simplified project data from the visual blueprint's API
            const response = await fetch('/visual/api/projects'); // API route in visual/routes.py
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            projectsData = await response.json(); // Store fetched data

            gridContainer.innerHTML = ''; // Clear loading message

            if (!projectsData || projectsData.length === 0) {
                 gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-muted"></p>';
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
            gridContainer.innerHTML = '<p class="text-center col-span-full p-10 text-error"></p>';
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
