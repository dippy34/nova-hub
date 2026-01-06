// Admin Panel JavaScript - Uses server API
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const refreshStatsBtn = document.getElementById('refresh-stats');
    const saveGaIdBtn = document.getElementById('save-ga-id');
    const createAdminForm = document.getElementById('create-admin-form');
    
    // Only set up refresh stats handler if the element exists
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', () => {
            loadAnalytics();
            loadAdminCount();
            loadFormsData();
        });
    }
    
    // Only set up GA ID handler if the element exists
    if (saveGaIdBtn) {
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
    }

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
            // Don't throw for 404s on optional endpoints like terminal-text (expected in local dev)
            if (response.status === 404 && (url.includes('/terminal-text') || url.includes('/save-terminal-text'))) {
                return { success: false, message: errorMessage };
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



    // Show dashboard
    function showDashboard(email) {
        loginScreen.style.display = 'none';
        adminDashboard.style.display = 'block';
        document.getElementById('admin-email').textContent = email;
        loadAnalytics();
        loadAdminCount();
        loadAdminList();
        if (document.getElementById('ga-measurement-id')) {
            loadGaId();
        }
        loadTerminalText();
        loadFormsData();
        setupFormsTabs();
        setupTerminalTextHandlers();
        setupAdminListHandlers();
    }

    // Load analytics data from Google Script
    async function loadAnalytics() {
        const scriptUrl = 'https://script.google.com/macros/s/AKfycbzGp9wKvzeTMp_IHu_Wr8ZCezqqNTl4z-54WKq_T5UywMfE2xRdWA6SIhyUHM0hbcOMew/exec';
        
        try {
            const response = await fetch(scriptUrl);
            const data = await response.json();
            
            if (data) {
                document.getElementById('total-views').textContent = data.totalViews !== undefined ? data.totalViews : '-';
                document.getElementById('active-users').textContent = data.currentActiveUsers !== undefined ? data.currentActiveUsers : '-';
                document.getElementById('screen-page-views').textContent = data.currentScreenPageViews !== undefined ? data.currentScreenPageViews : '-';
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
            document.getElementById('total-views').textContent = '-';
            document.getElementById('active-users').textContent = '-';
            document.getElementById('screen-page-views').textContent = '-';
        }
    }

    // Load admin count
    async function loadAdminCount() {
        try {
            const data = await apiRequest('/api/admin/count');
            
            if (data.success) {
                const count = data.count || '0';
                // Update both elements if they exist
                const adminCount = document.getElementById('admin-count');
                const adminCountText = document.getElementById('admin-count-text');
                if (adminCount) adminCount.textContent = count;
                if (adminCountText) adminCountText.textContent = count;
            }
        } catch (error) {
            console.error('Failed to load admin count:', error);
            const adminCount = document.getElementById('admin-count');
            const adminCountText = document.getElementById('admin-count-text');
            if (adminCount) adminCount.textContent = '-';
            if (adminCountText) adminCountText.textContent = '-';
        }
    }

    // Load admin list
    async function loadAdminList() {
        const listContainer = document.getElementById('admin-accounts-list');
        if (!listContainer) return;

        // Skip API call in local development to avoid 404 errors
        if (isLocalDev()) {
            listContainer.innerHTML = '<p>Admin list API is not available in local development. This feature will work when deployed to Cloudflare.</p>';
            return;
        }

        try {
            const data = await apiRequest('/api/admin/list');
            
            if (data.success && data.admins) {
                if (data.admins.length === 0) {
                    listContainer.innerHTML = '<p>No admin accounts found.</p>';
                    return;
                }

                // Get current user's email
                const currentUserEmail = localStorage.getItem('nova_admin_email') || '';

                listContainer.innerHTML = data.admins.map((admin, index) => {
                    const isCurrentUser = admin.email.toLowerCase() === currentUserEmail.toLowerCase();
                    const canDelete = !isCurrentUser && data.admins.length > 1;
                    
                    return `
                        <div class="suggestion-item" data-email="${admin.email.replace(/"/g, '&quot;')}">
                            <div class="suggestion-header">
                                <span class="suggestion-type">👤 Admin Account</span>
                                ${isCurrentUser ? '<span style="color: #00ff00; margin-left: 10px;">(You)</span>' : ''}
                            </div>
                            <div class="suggestion-title">${admin.email.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                            <div class="suggestion-actions" style="margin-top: 10px;">
                                ${canDelete ? `<button class="delete-suggestion-btn" onclick="deleteAdminAccount('${admin.email.replace(/'/g, "\\'")}')">Delete</button>` : '<span style="color: #aaa;">Cannot delete (your account or last admin)</span>'}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                listContainer.innerHTML = '<p>Failed to load admin accounts.</p>';
            }
        } catch (error) {
            console.error('Failed to load admin list:', error);
            listContainer.innerHTML = '<p>Failed to load admin accounts.</p>';
        }
    }

    // Setup admin list handlers
    function setupAdminListHandlers() {
        const refreshBtn = document.getElementById('refresh-admin-list-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                loadAdminList();
                loadAdminCount();
            });
        }
    }

    // Delete admin account
    window.deleteAdminAccount = async function(email) {
        // Skip API call in local development
        if (isLocalDev()) {
            alert('Admin account deletion is not available in local development. This feature will work when deployed to Cloudflare.');
            return;
        }

        if (!confirm(`Are you sure you want to delete the admin account "${email}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await apiRequest('/api/admin/delete-admin', {
                method: 'POST',
                body: JSON.stringify({ email })
            });

            if (response.success) {
                // Reload the admin list and count
                loadAdminList();
                loadAdminCount();
                alert('Admin account deleted successfully.');
            } else {
                alert('Failed to delete admin account: ' + (response.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting admin account:', error);
            alert('Error deleting admin account: ' + (error.message || 'Please try again.'));
        }
    };

    // Load GA ID
    async function loadGaId() {
        const gaIdInput = document.getElementById('ga-measurement-id');
        if (!gaIdInput) return;
        
        try {
            const data = await apiRequest('/api/admin/ga-id');
            
            if (data.success && data.gaId) {
                gaIdInput.value = data.gaId;
            }
        } catch (error) {
            console.error('Failed to load GA ID:', error);
        }
    }

    // Create admin account handler
    createAdminForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('new-admin-email').value;
        const password = document.getElementById('new-admin-password').value;
        const statusDiv = document.getElementById('create-admin-status');
        
        statusDiv.textContent = '';
        statusDiv.style.display = 'none';

        try {
            // Create the admin account
            const createResponse = await apiRequest('/api/admin/create-account', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });

            if (!createResponse.success) {
                statusDiv.textContent = createResponse.message || 'Failed to create admin account';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.display = 'block';
                return;
            }

            // Commit changes to git
            statusDiv.textContent = 'Admin account created. Committing to git...';
            statusDiv.style.color = '#00ff00';
            statusDiv.style.display = 'block';

            try {
                const commitResponse = await apiRequest('/api/admin/commit-changes', {
                    method: 'POST',
                    body: JSON.stringify({ message: `Add admin account: ${email}` })
                });

                if (commitResponse.success) {
                    statusDiv.textContent = 'Admin account created and committed to git successfully!';
                    statusDiv.style.color = '#00ff00';
                    
                    // Clear form
                    document.getElementById('new-admin-email').value = '';
                    document.getElementById('new-admin-password').value = '';
                    
                    // Refresh admin count and list
                    setTimeout(() => {
                        loadAdminCount();
                        loadAdminList();
                    }, 500);
                } else {
                    statusDiv.textContent = 'Account created but failed to commit: ' + (commitResponse.message || 'Unknown error');
                    statusDiv.style.color = '#ffaa00';
                }
            } catch (commitError) {
                statusDiv.textContent = 'Account created but failed to commit: ' + (commitError.message || 'Please commit manually');
                statusDiv.style.color = '#ffaa00';
            }
        } catch (error) {
            statusDiv.textContent = error.message || 'Failed to create admin account. Please try again.';
            statusDiv.style.color = '#ff0000';
            statusDiv.style.display = 'block';
            console.error('Create admin error:', error);
        }
    });

    // Check if running in local development
    function isLocalDev() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' || 
               window.location.port === '3000' ||
               window.location.hostname.includes('localhost');
    }

    // Load terminal text
    async function loadTerminalText() {
        // Skip API call in local development to avoid 404 errors
        if (isLocalDev()) {
            return;
        }
        
        try {
            const data = await apiRequest('/api/admin/terminal-text');
            
            if (data && data.success && data.data) {
                const welcomeTextarea = document.getElementById('terminal-welcome-lines');
                const statusInput = document.getElementById('terminal-status-text');
                
                if (welcomeTextarea) {
                    welcomeTextarea.value = (data.data.welcomeLines || []).join('\n');
                }
                if (statusInput) {
                    statusInput.value = data.data.statusText || 'If you see this, it loaded.';
                }
            }
        } catch (error) {
            // Silently fail - terminal text is optional
        }
    }

    // Setup terminal text handlers
    function setupTerminalTextHandlers() {
        const saveBtn = document.getElementById('save-terminal-text-btn');
        if (!saveBtn) return;

        saveBtn.addEventListener('click', async () => {
            const welcomeTextarea = document.getElementById('terminal-welcome-lines');
            const statusInput = document.getElementById('terminal-status-text');
            const statusDiv = document.getElementById('terminal-text-status');
            
            if (!welcomeTextarea || !statusInput) return;

            statusDiv.textContent = '';
            statusDiv.style.display = 'none';

            const welcomeLines = welcomeTextarea.value.split('\n').filter(line => line.trim() !== '');
            const statusText = statusInput.value.trim();

            if (welcomeLines.length === 0 || !statusText) {
                statusDiv.textContent = 'Please enter at least one welcome line and status text.';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.display = 'block';
                return;
            }

            // Skip API call in local development
            if (isLocalDev()) {
                statusDiv.textContent = 'Terminal text API is not available in local development. Changes will work when deployed to Cloudflare.';
                statusDiv.style.color = '#ffaa00';
                statusDiv.style.display = 'block';
                return;
            }

            try {
                const response = await apiRequest('/api/admin/save-terminal-text', {
                    method: 'POST',
                    body: JSON.stringify({ welcomeLines, statusText })
                });

                if (response && response.success) {
                    statusDiv.textContent = 'Terminal text saved successfully!';
                    statusDiv.style.color = '#00ff00';
                    statusDiv.style.display = 'block';
                } else {
                    statusDiv.textContent = response?.message || 'Failed to save terminal text.';
                    statusDiv.style.color = '#ff0000';
                    statusDiv.style.display = 'block';
                }
            } catch (error) {
                statusDiv.textContent = error.message || 'Failed to save terminal text. Please try again.';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.display = 'block';
            }
        });
    }

    // Setup forms tabs
    function setupFormsTabs() {
        const tabs = document.querySelectorAll('#forms-results-container .suggestion-tab');
        const contents = document.querySelectorAll('#forms-results-container .suggestions-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');
                
                // Remove active class from all tabs and contents in forms container
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    // Load Google Forms data
    async function loadFormsData() {
        const formsUrl = 'https://script.google.com/macros/s/AKfycbzYrrrgW8M1uK2gNifn5KBW8SJPzE9P-W7C51ocZHAQBpKkJnMl7ISzuyd_qpF8DZdjpA/exec';
        
        try {
            const response = await fetch(formsUrl);
            const data = await response.json();
            
            // Display Bug Reports
            if (data['Bug Reports'] && data['Bug Reports'].responses) {
                displayFormsData('forms-bug-reports-list', data['Bug Reports'].responses, 'bug');
            } else {
                document.getElementById('forms-bug-reports-list').innerHTML = '<p>No bug reports from forms yet.</p>';
            }
            
            // Display Game Requests
            if (data['Game Requests'] && data['Game Requests'].responses) {
                displayFormsData('forms-game-requests-list', data['Game Requests'].responses, 'game');
            } else {
                document.getElementById('forms-game-requests-list').innerHTML = '<p>No game requests from forms yet.</p>';
            }
        } catch (error) {
            console.error('Failed to load forms data:', error);
            document.getElementById('forms-bug-reports-list').innerHTML = '<p>Failed to load bug reports from forms.</p>';
            document.getElementById('forms-game-requests-list').innerHTML = '<p>Failed to load game requests from forms.</p>';
        }
    }

    // Display forms data
    function displayFormsData(containerId, responses, type) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (!responses || responses.length === 0) {
            container.innerHTML = '<p>No ' + (type === 'bug' ? 'bug reports' : 'game requests') + ' from forms yet.</p>';
            return;
        }

        // Sort responses by timestamp (newest first)
        const sortedResponses = [...responses].sort((a, b) => {
            const dateA = a.Timestamp ? new Date(a.Timestamp).getTime() : 0;
            const dateB = b.Timestamp ? new Date(b.Timestamp).getTime() : 0;
            return dateB - dateA; // Descending order (newest first)
        });

        container.innerHTML = sortedResponses.map((response, index) => {
            const timestamp = response.Timestamp ? new Date(response.Timestamp).toLocaleString() : 'Unknown date';
            const typeIcon = type === 'bug' ? '🐛' : '🎮';
            const typeLabel = type === 'bug' ? 'Bug Report' : 'Game Request';
            
            // Get the main fields based on type
            let title = '';
            let description = '';
            let steps = '';
            let email = '';
            
            if (type === 'bug') {
                title = response['what glitch is it'] || 'Bug Report';
                description = response['Tell me about the glitch'] || 'No description provided.';
                steps = response['How do you get the glitch, (step 1, step 2, step 3 etc)'] || '';
                email = response['email so I might get back to you (optional)'] || '';
            } else {
                title = response['What game would you like me to add? BE SPECIFIC'] || 'Game Request';
                email = response['your email so i might reach back to you if I fixed the problem NOT GARUNTEED(optional)'] || '';
            }
            
            return `
                <div class="suggestion-item" data-index="${index}">
                    <div class="suggestion-header">
                        <span class="suggestion-type">${typeIcon} ${typeLabel}</span>
                        <span class="suggestion-date">${timestamp}</span>
                    </div>
                    <div class="suggestion-title">${(title || 'Untitled').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
                    ${description ? `<div class="suggestion-description">${(description || 'No description provided.').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>` : ''}
                    ${steps ? `<div class="suggestion-steps"><strong>Steps to reproduce:</strong> ${steps.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>` : ''}
                    <div class="suggestion-meta">
                        ${email ? `<span class="suggestion-email">Email: ${email.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>` : '<span class="suggestion-email">Email: Not provided</span>'}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Setup refresh forms button
    const refreshFormsBtn = document.getElementById('refresh-forms-btn');
    if (refreshFormsBtn) {
        refreshFormsBtn.addEventListener('click', () => {
            loadFormsData();
        });
    }

    // Auto-refresh analytics every 30 seconds
    setInterval(() => {
        if (adminDashboard.style.display !== 'none') {
            loadAnalytics();
            loadFormsData();
        }
    }, 30000);

    // Initialize on page load
    init();
});
