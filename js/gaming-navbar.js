// Gaming Navbar Component
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';
    
    const navbarHTML = `
        <nav class="gaming-navbar">
            <a href="/index.html" class="logo">NOVA HUB</a>
            <ul class="nav-links">
                <li><a href="/suggest.html" class="${currentPage === 'suggest.html' ? 'active' : ''}">Bug Reports & Suggestions</a></li>
                <li><a href="/index.html" class="${currentPage === 'index.html' ? 'active' : ''}">Home</a></li>
                <li><a href="/projects.html" class="${currentPage === 'projects.html' ? 'active' : ''}">Games</a></li>
                <li><a href="/apps.html" class="${currentPage === 'apps.html' ? 'active' : ''}">Apps</a></li>
                <li><a href="/other.html" class="${currentPage === 'other.html' ? 'active' : ''}">Other</a></li>
                <li><a href="/settings.html" class="${currentPage === 'settings.html' ? 'active' : ''}">Settings</a></li>
                <li><a href="/about.html" class="${currentPage === 'about.html' ? 'active' : ''}">Hacks</a></li>
            </ul>
        </nav>
    `;
    
    // Insert navbar at the beginning of body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Add toggle button for navbar
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'gaming-nav-toggle';
    toggleBtn.className = 'gaming-nav-toggle';
    toggleBtn.innerHTML = '▲';
    toggleBtn.title = 'Toggle navigation';
    toggleBtn.addEventListener('click', toggleGamingNav);
    document.body.appendChild(toggleBtn);
    
    // Note: Theme class is managed by main.js based on selected theme
    // Don't force add gaming-theme here, let main.js handle it
    
    // Add panic button if enabled - use setTimeout to ensure DOM is ready
    setTimeout(() => {
        if (typeof window.updatePanicButton === 'function') {
            window.updatePanicButton();
        }
    }, 100);
});

// Toggle navigation bar collapse/expand
function toggleGamingNav() {
    const navbar = document.querySelector('.gaming-navbar');
    const toggleBtn = document.getElementById('gaming-nav-toggle');
    if (navbar && toggleBtn) {
        navbar.classList.toggle('collapsed');
        toggleBtn.classList.toggle('collapsed');
        toggleBtn.textContent = navbar.classList.contains('collapsed') ? '▼' : '▲';
    }
}

// Make function globally accessible
window.toggleGamingNav = toggleGamingNav;

// Panic Button Functions (for all pages)
window.updatePanicButton = function() {
    // Migration: check localStorage first, then cookie
    let enabled = localStorage.getItem('novahub.panicEnabled') === 'true';
    if (enabled) {
        setCookie('novahub.panicEnabled', 'true');
        localStorage.removeItem('novahub.panicEnabled');
    } else {
        enabled = getCookie('novahub.panicEnabled') === 'true';
    }
    
    if (enabled) {
        // Check if button already exists
        let panicButton = document.getElementById('panicButton');
        
        if (!panicButton) {
            // Create panic button
            panicButton = document.createElement('button');
            panicButton.id = 'panicButton';
            panicButton.className = 'panic-button';
            panicButton.innerHTML = '🚨';
            panicButton.onclick = window.activatePanic;
            document.body.appendChild(panicButton);
        } else {
            panicButton.style.display = 'flex';
        }
    } else {
        const panicButton = document.getElementById('panicButton');
        if (panicButton) {
            panicButton.style.display = 'none';
        }
    }
};

window.activatePanic = function() {
    // Migration: check localStorage first, then cookie
    let panicUrl = localStorage.getItem('novahub.panicUrl');
    if (panicUrl) {
        setCookie('novahub.panicUrl', panicUrl);
        localStorage.removeItem('novahub.panicUrl');
    } else {
        panicUrl = getCookie('novahub.panicUrl') || getCookie('panicurl') || 'https://google.com';
    }
    window.location.href = panicUrl;
};

// Also check on window load in case DOMContentLoaded already fired
if (document.readyState === 'loading') {
    // DOMContentLoaded hasn't fired yet, wait for it
} else {
    // DOMContentLoaded already fired, check panic button now
    setTimeout(() => {
        if (typeof window.updatePanicButton === 'function') {
            window.updatePanicButton();
        }
    }, 100);
}

// Also check when window fully loads
window.addEventListener('load', function() {
    setTimeout(() => {
        if (typeof window.updatePanicButton === 'function') {
            window.updatePanicButton();
        }
    }, 100);
});


