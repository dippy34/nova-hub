// Mobile menu functionality
window.toggleMobileMenu = function() {
    const menu = document.getElementById('mobile-menu');
    if (!menu) return;
    
    menu.classList.toggle('active');
    document.body.classList.toggle('menu-open');
}

// Initialize mobile menu
function initializeMobileMenu() {
    // Create mobile menu if it doesn't exist
    if (!document.getElementById('mobile-menu')) {
        const mobileMenu = document.createElement('div');
        mobileMenu.id = 'mobile-menu';
        mobileMenu.className = 'mobile-menu';
        mobileMenu.innerHTML = `
            <div class="mobile-menu-content">
                <button class="mobile-menu-close" onclick="toggleMobileMenu()">
                    <i class="fa-solid fa-xmark navbar-icon"></i>
                </button>
                <div class="mobile-menu-links">
                    <a class="navbar-link" href="/library.html">
                        <i class="fa-solid fa-gamepad navbar-icon"></i>Games
                    </a>
                    <a class="navbar-link" href="/settings.html">
                        <i class="fa-duotone fa-gear navbar-icon"></i>Settings
                    </a>
                    <a class="navbar-link" href="https://discord.gg/xjMnZn3R5f" target="_blank">
                        <i class="fa-brands fa-discord navbar-icon"></i>Discord
                    </a>
                </div>
            </div>
        `;
        document.body.appendChild(mobileMenu);
    }
}

// Initialize when navbar is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if navbar is already loaded
    if (document.getElementById('fixed-nav-bar')) {
        initializeMobileMenu();
    } else {
        // Wait for navbar to be loaded
        const observer = new MutationObserver((mutations) => {
            if (document.getElementById('fixed-nav-bar')) {
                initializeMobileMenu();
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}); 