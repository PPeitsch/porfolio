function initializeDraggableWindow(config) {
    const {
        windowId,
        titleBarId,
        contentId,
        closeBtnId,
        minimizeBtnId,
        maximizeBtnId,
        backButtonId,
    } = config;

    const windowEl = document.getElementById(windowId);
    if (!windowEl || windowEl.dataset.initialized) {
        return;
    }
    windowEl.dataset.initialized = "true";

    console.log(`Initializing Draggable Window: #${windowId}`);

    // --- DOM Element Selection ---
    const titleBar = document.getElementById(titleBarId);
    const closeBtn = document.getElementById(closeBtnId);
    const minimizeBtn = document.getElementById(minimizeBtnId);
    const maximizeBtn = document.getElementById(maximizeBtnId);
    const backButton = document.getElementById(backButtonId);

    if (!titleBar || !closeBtn || !minimizeBtn || !maximizeBtn || !backButton) {
        console.error(`One or more essential window elements for #${windowId} are missing!`);
        return;
    }

    // --- Window State Management ---
    let windowState = "normal";
    let stateBeforeMinimize = "normal";
    let lastPosition = { top: windowEl.offsetTop, left: windowEl.offsetLeft };

    function centerWindow() {
        const viewportWidth = document.documentElement.clientWidth;
        const viewportHeight = document.documentElement.clientHeight;
        const defaultWidth = Math.min(720, viewportWidth * 0.9);
        const defaultHeight = Math.min(500, viewportHeight * 0.9);
        const newLeft = (viewportWidth - defaultWidth) / 2;
        const newTop = (viewportHeight - defaultHeight) / 2;
        windowEl.style.width = `${defaultWidth}px`;
        windowEl.style.height = `${defaultHeight}px`;
        windowEl.style.left = `${newLeft}px`;
        windowEl.style.top = `${newTop}px`;
        lastPosition = { top: newTop, left: newLeft };
    }

    // --- Window Controls Logic ---
    function handleClose() { backButton.click(); }
    function handleMinimize() {
        if (windowState !== "minimized") {
            stateBeforeMinimize = windowState;
            windowState = "minimized";
            windowEl.classList.add("minimized");
            windowEl.classList.remove("maximized");
        }
    }
    function handleRestore() {
        if (windowState === "minimized") {
            windowEl.classList.remove("minimized");
            windowState = stateBeforeMinimize;
            if (windowState === "maximized") {
                windowEl.classList.add("maximized");
            }
        } else if (windowState === "maximized") { handleMaximize(); }
    }
    function handleMaximize() {
        if (windowState === "maximized") {
            windowEl.classList.remove("maximized");
            windowEl.style.top = `${lastPosition.top}px`;
            windowEl.style.left = `${lastPosition.left}px`;
            windowState = "normal";
        } else {
            if (windowState === "minimized") { windowEl.classList.remove("minimized"); }
            lastPosition = { top: windowEl.offsetTop, left: windowEl.offsetLeft };
            windowEl.classList.add("maximized");
            windowEl.style.top = "";
            windowEl.style.left = "";
            windowState = "maximized";
        }
    }
    function handleReset() {
        windowEl.classList.remove('maximized', 'minimized');
        centerWindow();
        windowState = 'normal';
    }

    // --- Window Dragging Logic ---
    let isDragging = false;
    let offsetX, offsetY;
    function onMouseDown(e) {
        if (e.button !== 0 || e.target.classList.contains("control-btn")) { return; }
        if (windowState === "maximized") return;
        isDragging = true;
        offsetX = e.clientX - windowEl.offsetLeft;
        offsetY = e.clientY - windowEl.offsetTop;
        windowEl.classList.add('is-dragging');
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
        document.addEventListener("mouseleave", onMouseUp);
    }
    function onMouseMove(e) {
        if (!isDragging) return;
        let newX = e.clientX - offsetX;
        let newY = e.clientY - offsetY;
        const viewportWidth = document.documentElement.clientWidth;
        const viewportHeight = document.documentElement.clientHeight;
        const windowWidth = windowEl.offsetWidth;
        const windowHeight = windowEl.offsetHeight;
        newX = Math.max(0, Math.min(newX, viewportWidth - windowWidth));
        newY = Math.max(0, Math.min(newY, viewportHeight - windowHeight));
        windowEl.style.left = `${newX}px`;
        windowEl.style.top = `${newY}px`;
    }
    function onMouseUp() {
        if (!isDragging) return;
        isDragging = false;
        windowEl.classList.remove('is-dragging');
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.removeEventListener("mouseleave", onMouseUp);
    }

    // --- Event Listeners ---
    closeBtn.addEventListener("click", handleClose);
    minimizeBtn.addEventListener("click", () => {
        if (windowState === 'minimized') handleRestore();
        else handleMinimize();
    });
    maximizeBtn.addEventListener("click", handleMaximize);
    titleBar.addEventListener("dblclick", handleMaximize);
    titleBar.addEventListener("mousedown", onMouseDown);

    // Add a public reset method if needed by the specific view
    if (!windowEl.reset) {
        windowEl.reset = handleReset;
    }

    // --- Initial Setup ---
    centerWindow();

    return {
        reset: handleReset,
        close: handleClose,
        minimize: handleMinimize,
        maximize: handleMaximize,
    };
}
