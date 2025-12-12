/**
 * UI Helpers Module
 * 
 * Small, reusable UI utility functions.
 */

/**
 * Remove VR button from A-Frame scene
 */
function removeVRButton() {
    const vrButton = document.querySelector('.a-enter-vr, .a-enter-vr-button, .a-enter-vr-fullscreen');
    if (vrButton) {
        vrButton.remove();
    }
}

// Remove VR button immediately and on interval
setInterval(removeVRButton, 100);

/**
 * Toggle burger menu visibility
 */
function toggleBurgerMenu() {
    const menu = document.getElementById('burger-menu');
    const btn = document.getElementById('burger-menu-btn');
    if (menu && btn) {
        if (menu.style.display === 'none' || menu.style.display === '') {
            menu.style.display = 'block';
        } else {
            menu.style.display = 'none';
        }
    }
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.getElementById('burger-menu');
    const btn = document.getElementById('burger-menu-btn');
    if (menu && btn && !menu.contains(event.target) && !btn.contains(event.target)) {
        menu.style.display = 'none';
    }
});

// Export functions globally
if (typeof window !== 'undefined') {
    window.removeVRButton = removeVRButton;
    window.toggleBurgerMenu = toggleBurgerMenu;
}

