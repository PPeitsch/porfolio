function initializeDraggableWindow(config) {
    const {
        windowId,
        titleBarId,
        closeBtnId,
        minimizeBtnId,
        maximizeBtnId,
        onClose, // New callback function
    } = config;

    const windowEl = document.getElementById(windowId);
    if (!windowEl || windowEl.dataset.initialized) {
        return { reset: () => {}, close: () => {}, minimize: () => {}, maximize: () => {} };
    }
    windowEl.dataset.initialized = "true";

    console.log(`Initializing Draggable Window: #${windowId}`);

    const titleBar = document.getElementById(titleBarId);
    const closeBtn = document.getElementById(closeBtnId);
    const minimizeBtn = document.getElementById(minimizeBtnId);
    const maximizeBtn = document.getElementById(maximizeBtnId);

    // The check for backButton is removed, as it's no longer a dependency.
    if (!titleBar || !closeBtn || !minimizeBtn || !maximizeBtn) {
        console.error(`One or more essential window elements for #${windowId} are missing!`);
        return { reset: () => {}, close: () => {}, minimize: () => {}, maximize: () => {} };
    }

    let windowState = "normal"; // 'normal', 'maximized', 'minimized'
    let lastPosition = { top: 0, left: 0, width: 0, height: 0 };

    function focusFirstInput() {
        const firstInput = windowEl.querySelector('input[type="text"], textarea');
        if (firstInput) {
            firstInput.focus();
        }
    }

    function saveLastPosition() {
        if (windowState === "normal") {
            lastPosition = {
                top: windowEl.offsetTop,
                left: windowEl.offsetLeft,
                width: windowEl.offsetWidth,
                height: windowEl.offsetHeight,
            };
        }
    }

    function restoreLastPosition() {
        windowEl.style.top = `${lastPosition.top}px`;
        windowEl.style.left = `${lastPosition.left}px`;
        windowEl.style.width = `${lastPosition.width}px`;
        windowEl.style.height = `${lastPosition.height}px`;
    }

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

        saveLastPosition();
    }

    // handleClose now calls the provided callback function.
    function handleClose() {
        if (typeof onClose === 'function') {
            onClose();
        } else {
            console.error('onClose callback is not a function!');
        }
    }

    function handleMinimize() {
        if (windowState !== 'minimized') {
            saveLastPosition();
            windowState = 'minimized';
            windowEl.classList.add('minimized');
            windowEl.classList.remove('maximized');
        } else {
            windowEl.classList.remove('minimized');
            windowState = 'normal';
            restoreLastPosition();
            focusFirstInput();
        }
    }

    function handleMaximize() {
        if (windowState !== 'maximized') {
            saveLastPosition();
            windowState = 'maximized';
            windowEl.classList.add('maximized');
            windowEl.classList.remove('minimized');
        } else {
            windowState = 'normal';
            windowEl.classList.remove('maximized');
            restoreLastPosition();
        }
        focusFirstInput();
    }

    let isDragging = false;
    let offsetX, offsetY;
    function onMouseDown(e) {
        if (e.button !== 0 || e.target.classList.contains("control-btn")) return;
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
        saveLastPosition();
        windowEl.classList.remove('is-dragging');
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.removeEventListener("mouseleave", onMouseUp);
    }

    closeBtn.addEventListener("click", handleClose);
    minimizeBtn.addEventListener("click", handleMinimize);
    maximizeBtn.addEventListener("click", handleMaximize);
    titleBar.addEventListener("dblclick", handleMaximize);
    titleBar.addEventListener("mousedown", onMouseDown);

    centerWindow();
    focusFirstInput();

    return {
        reset: centerWindow,
        close: handleClose,
        minimize: handleMinimize,
        maximize: handleMaximize,
    };
}
