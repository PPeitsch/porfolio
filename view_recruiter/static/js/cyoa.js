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
    let isLoading = false; // Prevent double clicks

    async function fetchStepData(stepId) {
        if (isLoading) return; // Don't fetch if already loading
        isLoading = true;
        console.log(`Fetching data for step: ${stepId}`);
        if(statusElem) statusElem.textContent = 'Loading...';
        storyContent.classList.remove('loaded'); // Fade out content

        try {
            // --- Fetch from the REAL API endpoint ---
            const response = await fetch(`/recruiter/api/step/${encodeURIComponent(stepId)}`); // Use blueprint prefix
            if (!response.ok) {
                 let errorMsg = `Server error: ${response.status}`;
                 try {
                     const errorData = await response.json();
                     errorMsg = `Server error: ${errorData.error || response.statusText}`;
                 } catch(e) { /* ignore if response not json */ }
                throw new Error(errorMsg);
            }
            const data = await response.json();
            // --- End API Fetch ---

            renderStep(data);

        } catch (error) {
            console.error("Error fetching step data:", error);
            storyTextElem.textContent = `Error loading story step: ${error.message}. Please try going back or refreshing.`;
            choicesContainer.innerHTML = ''; // Clear choices on error
            if(statusElem) statusElem.textContent = 'Error';
            storyContent.classList.add('loaded'); // Show error message
        } finally {
             isLoading = false;
        }
    }

    function renderStep(data) {
        console.log("Rendering step:", data);
        currentStepId = data.step_id; // Update current step

        // --- Render Text (potentially with basic Markdown support) ---
        // Replace newline characters from backend text with <br> for HTML display
        // Basic Markdown-like formatting for **bold** (add more if needed)
        let formattedText = data.text.replace(/\n/g, '<br>');
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        storyTextElem.innerHTML = formattedText; // Use innerHTML to render <br> and <strong>

        choicesContainer.innerHTML = ''; // Clear previous choices

        if (data.choices && data.choices.length > 0) {
            data.choices.forEach(choice => {
                const button = document.createElement('button');
                button.innerHTML = choice.text; // Use innerHTML if choice text might contain basic formatting

                // Base classes
                button.className = 'cyoa-choice-button w-full text-left font-medium p-3 px-4 rounded-md border transition duration-150 ease-in-out';

                // Style based on choice type (navigation vs external link)
                if (choice.next_step) {
                    button.classList.add('bg-gray-50', 'hover:bg-gray-100', 'text-gray-700', 'border-gray-200');
                    button.dataset.nextStep = choice.next_step; // Store next step ID
                    button.addEventListener('click', handleChoiceClick);
                } else if (choice.url) {
                     button.classList.add('bg-blue-50', 'hover:bg-blue-100', 'text-blue-700', 'border-blue-200');
                    // Make it act like a link
                     button.onclick = () => window.open(choice.url, '_blank');
                     // Add an external link icon maybe
                     button.innerHTML += ' <i class="fas fa-external-link-alt fa-xs opacity-60"></i>';
                } else {
                    // Default style if neither next_step nor url
                     button.classList.add('bg-gray-50', 'text-gray-500', 'border-gray-200', 'cursor-not-allowed');
                     button.disabled = true;
                }
                choicesContainer.appendChild(button);
            });
        } else {
            // End of a path - provide a way back
            const restartButton = document.createElement('button');
            restartButton.textContent = 'Start Over';
            restartButton.className = 'cyoa-choice-button w-full text-left bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium p-3 px-4 rounded-md border border-indigo-200 transition duration-150 ease-in-out mt-4';
            restartButton.dataset.nextStep = 'start';
            restartButton.addEventListener('click', handleChoiceClick);
            choicesContainer.appendChild(restartButton);
        }

        if(statusElem) statusElem.textContent = ``; // Clear loading status or show step name: `Path: ${currentStepId}`;
        setTimeout(() => {
            storyContent.classList.add('loaded');
        }, 50); // Fade in content
    }

    function handleChoiceClick(event) {
        // Use currentTarget to ensure we get the button if click is on icon inside
        const button = event.currentTarget;
        const nextStepId = button.dataset.nextStep;
        if (nextStepId && !isLoading) { // Check isLoading flag
            fetchStepData(nextStepId);
        } else if (!isLoading) {
            console.warn("Choice button clicked without a next step ID.");
        }
    }

    // --- Initial Load ---
    fetchStepData(currentStepId); // Load the starting step ('start')
    console.log("Recruiter (CYOA) View Initialized.");

    // --- Cleanup Function ---
    window.cleanupRecruiterView = () => {
        console.log("Running cleanup for Recruiter view...");
        // If event listeners were delegated to container, remove them here.
        // Otherwise, removing the elements generally suffices for simple cases.
        // Example: choicesContainer.removeEventListener('click', handleChoiceClick); // If delegated
    };

} // End of initializeRecruiterView

// Make initializer globally accessible
window.initializeRecruiterView = initializeRecruiterView;
// Define cleanup function globally
window.cleanupRecruiterView = window.cleanupRecruiterView || (() => { console.log("Default Recruiter cleanup"); });
