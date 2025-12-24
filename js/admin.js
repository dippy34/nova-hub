// Admin Panel JavaScript - Uses server API
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const refreshStatsBtn = document.getElementById('refresh-stats');
    const saveGaIdBtn = document.getElementById('save-ga-id');

    // Get stored token
    function getToken() {
        return localStorage.getItem('nova_admin_token');
    }

    // Store token
    function setToken(token) {
        localStorage.setItem('nova_admin_token', token);
    }

    // Remove token
    function removeToken() {
        localStorage.removeItem('nova_admin_token');
        localStorage.removeItem('nova_admin_email');
    }

    // Make authenticated API request
    async function apiRequest(url, options = {}) {
        const token = getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired or invalid
            removeToken();
            showLogin();
            throw new Error('Session expired. Please login again.');
        }

        if (!response.ok) {
            let errorMessage = 'Request failed';
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || errorData.error || `HTTP ${response.status}: ${response.statusText}`;
            } catch (e) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        return response.json();
    }

    // Initialize - check if already logged in
    async function init() {
        const token = getToken();
        if (token) {
            try {
                // Verify token is still valid
                const response = await fetch('/api/admin/verify', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    showDashboard(data.email);
                    return;
                }
            } catch (error) {
                console.error('Token verification failed:', error);
            }
        }
        // If no token or verification failed, show login
        showLogin();
    }

    // Show login screen
    function showLogin() {
        loginScreen.style.display = 'block';
        adminDashboard.style.display = 'none';
        document.getElementById('login-email').value = '';
        document.getElementById('login-password').value = '';
        document.getElementById('login-error').textContent = '';
        document.getElementById('login-error').style.display = 'none';
    }

    // Login form handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        errorDiv.textContent = '';
        errorDiv.style.display = 'none';

        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                errorDiv.textContent = data.message || 'Invalid credentials. Please check your email and password.';
                errorDiv.style.display = 'block';
                return;
            }

            // Store token and email
            setToken(data.token);
            localStorage.setItem('nova_admin_email', data.email);
            showDashboard(data.email);
        } catch (error) {
            errorDiv.textContent = 'Error during login. Please check your connection and try again.';
            errorDiv.style.display = 'block';
            console.error('Login error:', error);
        }
    });

    // Logout handler
    logoutBtn.addEventListener('click', () => {
        removeToken();
        showLogin();
    });

    // Save GA ID handler
    saveGaIdBtn.addEventListener('click', async () => {
        const gaId = document.getElementById('ga-measurement-id').value;
        const statusDiv = document.getElementById('ga-status');
        
        statusDiv.textContent = '';
        statusDiv.style.display = 'none';

        try {
            await apiRequest('/api/admin/save-ga-id', {
                method: 'POST',
                body: JSON.stringify({ gaId })
            });
            
            statusDiv.textContent = 'Google Analytics ID saved successfully.';
            statusDiv.style.color = '#00ff00';
            statusDiv.style.display = 'block';
            
            // Refresh analytics after saving
            setTimeout(() => {
                loadAnalytics();
            }, 1000);
        } catch (error) {
            statusDiv.textContent = error.message || 'Failed to save GA ID.';
            statusDiv.style.color = '#ff0000';
            statusDiv.style.display = 'block';
        }
    });

    // Refresh stats handler
    refreshStatsBtn.addEventListener('click', () => {
        loadAnalytics();
        loadAdminCount();
    });

    // Show dashboard
    function showDashboard(email) {
        loginScreen.style.display = 'none';
        adminDashboard.style.display = 'block';
        document.getElementById('admin-email').textContent = email;
        loadAnalytics();
        loadAdminCount();
        loadGaId();
        loadSuggestions();
        setupSuggestionTabs();
    }

    // Load analytics data
    async function loadAnalytics() {
        try {
            const data = await apiRequest('/api/admin/analytics');
            
            if (data.success) {
                document.getElementById('live-users').textContent = data.liveUsers || '0';
                document.getElementById('total-users').textContent = data.totalUsers || '0';
                document.getElementById('today-visits').textContent = data.todayVisits || '0';
                document.getElementById('page-views').textContent = data.pageViews || '0';
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
            // Show error or use defaults
            document.getElementById('live-users').textContent = '-';
            document.getElementById('total-users').textContent = '-';
            document.getElementById('today-visits').textContent = '-';
            document.getElementById('page-views').textContent = '-';
        }
    }

    // Load admin count
    async function loadAdminCount() {
        try {
            const data = await apiRequest('/api/admin/count');
            
            if (data.success) {
                document.getElementById('admin-count').textContent = data.count || '0';
            }
        } catch (error) {
            console.error('Failed to load admin count:', error);
            document.getElementById('admin-count').textContent = '-';
        }
    }

    // Load GA ID
    async function loadGaId() {
        try {
            const data = await apiRequest('/api/admin/ga-id');
            
            if (data.success && data.gaId) {
                document.getElementById('ga-measurement-id').value = data.gaId;
            }
        } catch (error) {
            console.error('Failed to load GA ID:', error);
        }
    }

    // Setup suggestion tabs
    function setupSuggestionTabs() {
        const tabs = document.querySelectorAll('.suggestion-tab');
        const contents = document.querySelectorAll('.suggestions-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });
    }

    // Load suggestions and bug reports
    async function loadSuggestions() {
        try {
            const data = await apiRequest('/api/admin/suggestions');
            
            if (data.success && data.data) {
                console.log('Loaded suggestions data:', data.data);
                displaySuggestions('game-suggestions-list', data.data.gameSuggestions || [], 'game');
                displaySuggestions('feature-suggestions-list', data.data.featureSuggestions || [], 'feature');
                displaySuggestions('bug-reports-list', data.data.bugReports || [], 'bug');
            }
        } catch (error) {
            console.error('Failed to load suggestions:', error);
            document.getElementById('game-suggestions-list').innerHTML = '<p>Failed to load suggestions.</p>';
            document.getElementById('feature-suggestions-list').innerHTML = '<p>Failed to load suggestions.</p>';
            document.getElementById('bug-reports-list').innerHTML = '<p>Failed to load bug reports.</p>';
        }
    }

    // Display suggestions in a list
    function displaySuggestions(containerId, suggestions, type) {
        const container = document.getElementById(containerId);
        
        if (!suggestions || suggestions.length === 0) {
            container.innerHTML = '<p>No ' + (type === 'game' ? 'game suggestions' : type === 'feature' ? 'feature suggestions' : 'bug reports') + ' yet.</p>';
            return;
        }

        container.innerHTML = suggestions.map((suggestion, index) => {
            const date = suggestion.date ? new Date(suggestion.date).toLocaleDateString() : 'Unknown date';
            const typeIcon = type === 'game' ? '🎮' : type === 'feature' ? '💡' : '🐛';
            const typeLabel = type === 'game' ? 'Game' : type === 'feature' ? 'Feature' : 'Bug';
            
            return `
                <div class="suggestion-item" data-index="${index}" data-type="${type}">
                    <div class="suggestion-header">
                        <span class="suggestion-type">${typeIcon} ${typeLabel}</span>
                        <span class="suggestion-date">${date}</span>
                    </div>
                    <div class="suggestion-title">${(suggestion.title || 'Untitled').replace(/"/g, '&quot;')}</div>
                    <div class="suggestion-description">${(suggestion.description || suggestion.message || 'No description provided.').replace(/"/g, '&quot;')}</div>
                    ${suggestion.steps ? `<div class="suggestion-steps"><strong>Steps to reproduce:</strong> ${suggestion.steps.replace(/"/g, '&quot;')}</div>` : ''}
                    <div class="suggestion-meta">
                        ${suggestion.email ? `<span class="suggestion-email">Email: ${suggestion.email.replace(/"/g, '&quot;')}</span>` : '<span class="suggestion-email">Email: Not provided</span>'}
                        <span class="suggestion-ip">IP: ${suggestion.ip || 'Unknown'}</span>
                    </div>
                    <div class="suggestion-actions">
                        <button class="delete-suggestion-btn" onclick="deleteSuggestion('${type}', ${index})">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Delete suggestion
    window.deleteSuggestion = async function(type, index) {
        if (!confirm('Are you sure you want to delete this suggestion?')) {
            return;
        }

        try {
            // Ensure index is a number
            const indexNum = parseInt(index, 10);
            if (isNaN(indexNum)) {
                alert('Invalid index. Please refresh the page and try again.');
                return;
            }

            console.log('Deleting suggestion:', { type, index: indexNum });

            const response = await apiRequest('/api/admin/delete-suggestion', {
                method: 'POST',
                body: JSON.stringify({ type, index: indexNum })
            });

            if (response.success) {
                // Reload suggestions to refresh the display
                loadSuggestions();
            } else {
                alert('Failed to delete suggestion: ' + (response.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting suggestion:', error);
            alert('Error deleting suggestion: ' + (error.message || 'Please try again.'));
        }
    };

    // Auto-refresh analytics every 30 seconds
    setInterval(() => {
        if (adminDashboard.style.display !== 'none') {
            loadAnalytics();
        }
    }, 30000);

    // Initialize on page load
    init();
});
