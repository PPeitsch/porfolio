function initializeRecruiterView() {
    console.log("Attempting to initialize Recruiter (CYOA) View...");

    const container = document.getElementById('cyoa-container');
    const storyContent = document.getElementById('story-content');
    const storyTextElem = document.getElementById('story-text');
    const choicesContainer = document.getElementById('choices-container');
    const statusElem = document.getElementById('cyoa-status'); // Optional status element

    if (!container || !storyContent || !storyTextElem || !choicesContainer) {
        console.error("One or more CYOA elements are missing!");
        return; // Stop initialization
    }

    let currentStepId = 'start'; // Initial step identifier

    async function fetchStepData(stepId) {
        console.log(`Fetching data for step: ${stepId}`);
        statusElem.textContent = 'Loading...'; // Update status
        storyContent.classList.remove('loaded'); // Fade out content

        try {
            // TODO: In future step, fetch from the actual API endpoint
            // const response = await fetch(`/recruiter/api/step/${stepId}`);
            // if (!response.ok) throw new Error(`Server error: ${response.status}`);
            // const data = await response.json();

            // --- Mock Data for Step 3.1 ---
            await new Promise(resolve => setTimeout(resolve, 300)); // Simulate network delay
            let data;
            if (stepId === 'start') {
                 data = {
                    step_id: 'start',
                    text: "Welcome! I'm excited to show you around my portfolio. What aspect of my experience are you most interested in first?",
                    choices: [
                        { text: 'My core technical skills', next_step: 'skills_overview' },
                        { text: 'Projects demonstrating web development (Flask/FastAPI)', next_step: 'web_projects' },
                        { text: 'My experience with automation & APIs', next_step: 'automation_apis' },
                    ]
                };
            } else {
                 // Generic placeholder for other steps for now
                 data = {
                     step_id: stepId,
                     text: `You chose to explore '${stepId}'. (More content coming soon!) This is placeholder text for this path.`,
                     choices: [
                         { text: 'Go back to start', next_step: 'start' },
                         { text: 'Explore another placeholder', next_step: 'placeholder_2'}
                     ]
                 };
            }
             // --- End Mock Data ---

            renderStep(data);

        } catch (error) {
            console.error("Error fetching step data:", error);
            storyTextElem.textContent = `Error loading story: ${error.message}. Please try refreshing or going back.`;
            choicesContainer.innerHTML = ''; // Clear choices on error
            statusElem.textContent = 'Error';
            storyContent.classList.add('loaded'); // Show error message
        }
    }

    function renderStep(data) {
        console.log("Rendering step:", data);
        currentStepId = data.step_id; // Update current step

        storyTextElem.textContent = data.text;
        choicesContainer.innerHTML = ''; // Clear previous choices

        if (data.choices && data.choices.length > 0) {
            data.choices.forEach(choice => {
                const button = document.createElement('button');
                button.textContent = choice.text;
                // Use Tailwind classes if preferred, or fallback to CSS class
                button.className = 'cyoa-choice-button w-full text-left bg-gray-50 hover:bg-gray-100 text-gray-700 font-medium p-3 px-4 rounded-md border border-gray-200 transition duration-150 ease-in-out';
                button.dataset.nextStep = choice.next_step; // Store next step ID
                button.addEventListener('click', handleChoiceClick);
                choicesContainer.appendChild(button);
            });
        } else {
            // End of a path?
            choicesContainer.innerHTML = '<p class="text-gray-500 italic">-- End of this path --</p>';
            // Optionally add a "Restart" button
             const restartButton = document.createElement('button');
             restartButton.textContent = 'Start Over';
             restartButton.className = 'cyoa-choice-button w-full text-left bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium p-3 px-4 rounded-md border border-indigo-200 transition duration-150 ease-in-out mt-4';
             restartButton.dataset.nextStep = 'start';
             restartButton.addEventListener('click', handleChoiceClick);
             choicesContainer.appendChild(restartButton);
        }

        statusElem.textContent = `Step: ${currentStepId}`; // Update status
        // Use a slight delay for the fade-in effect to be noticeable after content update
        setTimeout(() => {
            storyContent.classList.add('loaded');
        }, 50); // Short delay
    }

    function handleChoiceClick(event) {
        const nextStepId = event.target.dataset.nextStep;
        if (nextStepId) {
            fetchStepData(nextStepId);
        } else {
            console.warn("Choice button clicked without a next step ID.");
        }
    }

    // --- Initial Load ---
    fetchStepData(currentStepId); // Load the starting step
    console.log("Recruiter (CYOA) View Initialized.");

    // --- Cleanup Function ---
    // Define a function to remove listeners when the view is unloaded
    window.cleanupRecruiterView = () => {
        console.log("Cleaning up Recruiter view listeners...");
        // Remove listeners from buttons dynamically? Or just let elements be destroyed.
        // If adding listeners to container, remove them here.
         choicesContainer.removeEventListener('click', handleChoiceClick); // Example if delegated
    };

} // End of initializeRecruiterView

// Make initializer globally accessible for selector.js
window.initializeRecruiterView = initializeRecruiterView;
// Define cleanup function globally as well
window.cleanupRecruiterView = window.cleanupRecruiterView || (() => {}); // Ensure it exists even if init fails