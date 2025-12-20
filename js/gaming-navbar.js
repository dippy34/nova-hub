// Gaming Navbar Component
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';
    
    const navbarHTML = `
        <nav class="gaming-navbar">
            <a href="/index.html" class="logo">NOVA HUB</a>
            <ul class="nav-links">
                <li><a href="/index.html" class="${currentPage === 'index.html' ? 'active' : ''}">Home</a></li>
                <li><a href="/projects.html" class="${currentPage === 'projects.html' ? 'active' : ''}">Games</a></li>
                <li><a href="/apps.html" class="${currentPage === 'apps.html' ? 'active' : ''}">Apps</a></li>
                <li><a href="/bookmarklets.html" class="${currentPage === 'bookmarklets.html' ? 'active' : ''}">Bookmarklets</a></li>
                <li><a href="/settings.html" class="${currentPage === 'settings.html' ? 'active' : ''}">Settings</a></li>
                <li><a href="/about.html" class="${currentPage === 'about.html' ? 'active' : ''}">About</a></li>
            </ul>
        </nav>
    `;
    
    // Insert navbar at the beginning of body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Add gaming theme class to body
    document.body.classList.add('gaming-theme');
});

