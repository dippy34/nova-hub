// Admin Panel JavaScript - Uses server API
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const refreshStatsBtn = document.getElementById('refresh-stats');
    const saveGaIdBtn = document.getElementById('save-ga-id');
    const changePasswordForm = document.getElementById('change-password-form');
    
    // Only set up refresh stats handler if the element exists
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', () => {
            loadAnalytics();
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
            // Only trigger logout if not explicitly disabled (for optional endpoints)
            if (options.skipLogoutOn401 !== true) {
                removeToken();
                showLogin();
            }
            const error = new Error('Session expired. Please login again.');
            error.status = 401;
            throw error;
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
                // Verify token is still valid with retry logic for KV eventual consistency
                let verified = false;
                for (let i = 0; i < 2; i++) {
                    const response = await fetch('/api/admin/verify', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        verified = true;
                        showDashboard();
                        return;
                    }
                    
                    // If 401 and first attempt, wait a bit and retry (KV might be eventually consistent)
                    if (response.status === 401 && i === 0) {
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                }
                
                // If verification failed after retries, token is invalid
                if (!verified) {
                    removeToken();
                }
            } catch (error) {
                // Only log errors in development
                if (isLocalDev()) {
                    console.error('Token verification failed:', error);
                }
                removeToken();
            }
        }
        // If no token or verification failed, show login
        showLogin();
    }

    // Show login screen
    function showLogin() {
        loginScreen.style.display = 'block';
        adminDashboard.style.display = 'none';
        document.getElementById('login-password').value = '';
        document.getElementById('login-error').textContent = '';
        document.getElementById('login-error').style.display = 'none';
    }

    // Login form handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
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
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                errorDiv.textContent = data.message || 'Invalid password. Please check your password.';
                errorDiv.style.display = 'block';
                return;
            }

            // Store token
            setToken(data.token);
            
            // Wait a bit for KV eventual consistency before verifying
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Verify token is actually available in KV before showing dashboard
            // Cloudflare KV has eventual consistency, so we need to wait a bit
            let verified = false;
            for (let i = 0; i < 5; i++) {
                try {
                    const verifyResponse = await fetch('/api/admin/verify', {
                        headers: {
                            'Authorization': `Bearer ${data.token}`
                        }
                    });
                    
                    if (verifyResponse.ok) {
                        verified = true;
                        break;
                    }
                } catch (error) {
                    // Continue to retry
                }
                
                // Wait before retrying (exponential backoff: 200ms, 400ms, 600ms, 800ms)
                if (i < 4) {
                    await new Promise(resolve => setTimeout(resolve, 200 * (i + 1)));
                }
            }
            
            if (verified) {
                showDashboard();
            } else {
                // Token verification failed after retries - this might be a KV configuration issue
                // Still show dashboard since login was successful - user can refresh if needed
                console.warn('Token verification failed after login, but proceeding anyway. If you see issues, please refresh the page.');
                showDashboard();
            }
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
    function showDashboard() {
        loginScreen.style.display = 'none';
        adminDashboard.style.display = 'block';
        
        // Load non-authenticated data immediately
        loadAnalytics();
        loadFormsData();
        setupFormsTabs();
        setupTerminalTextHandlers();
        setupChangePasswordHandler();
        
        // Load authenticated endpoints after a short delay to ensure token is available in KV
        setTimeout(() => {
            if (document.getElementById('ga-measurement-id')) {
                loadGaId();
            }
            loadTerminalText();
        }, 500); // 500ms delay to ensure token is available in Cloudflare KV
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


    // Load GA ID with retry logic
    async function loadGaId(retryCount = 0) {
        const gaIdInput = document.getElementById('ga-measurement-id');
        if (!gaIdInput) return;
        
        try {
            // Use skipLogoutOn401 to prevent logout if token verification fails for optional endpoint
            const data = await apiRequest('/api/admin/ga-id', { skipLogoutOn401: true });
            
            if (data.success && data.gaId) {
                gaIdInput.value = data.gaId;
            }
        } catch (error) {
            // Retry once if we get a 401 (token might not be in KV yet) and we haven't retried
            if (error.status === 401 && retryCount === 0) {
                setTimeout(() => loadGaId(1), 1000);
                return;
            }
            // Only log in development, not in production to avoid console noise
            if (isLocalDev()) {
                console.error('Failed to load GA ID:', error);
            }
        }
    }

    // Setup change password handler
    function setupChangePasswordHandler() {
        if (!changePasswordForm) return;
        
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const statusDiv = document.getElementById('change-password-status');
            
            statusDiv.textContent = '';
            statusDiv.style.display = 'none';

            // Validate passwords match
            if (newPassword !== confirmPassword) {
                statusDiv.textContent = 'New passwords do not match.';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.display = 'block';
                return;
            }

            // Skip API call in local development
            if (isLocalDev()) {
                statusDiv.textContent = 'Password change is not available in local development. This feature will work when deployed to Cloudflare.';
                statusDiv.style.color = '#ffaa00';
                statusDiv.style.display = 'block';
                return;
            }

            try {
                const response = await apiRequest('/api/admin/change-password', {
                    method: 'POST',
                    body: JSON.stringify({ currentPassword, newPassword })
                });

                if (response.success) {
                    statusDiv.textContent = 'Password changed successfully!';
                    statusDiv.style.color = '#00ff00';
                    statusDiv.style.display = 'block';
                    
                    // Clear form
                    document.getElementById('current-password').value = '';
                    document.getElementById('new-password').value = '';
                    document.getElementById('confirm-password').value = '';
                } else {
                    statusDiv.textContent = response.message || 'Failed to change password.';
                    statusDiv.style.color = '#ff0000';
                    statusDiv.style.display = 'block';
                }
            } catch (error) {
                statusDiv.textContent = error.message || 'Failed to change password. Please try again.';
                statusDiv.style.color = '#ff0000';
                statusDiv.style.display = 'block';
                console.error('Change password error:', error);
            }
        });
    }

    // Check if running in local development
    function isLocalDev() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' || 
               window.location.port === '3000' ||
               window.location.hostname.includes('localhost');
    }

    // Load terminal text with retry logic
    async function loadTerminalText(retryCount = 0) {
        // Skip API call in local development to avoid 404 errors
        if (isLocalDev()) {
            return;
        }
        
        try {
            // Use skipLogoutOn401 to prevent logout if token verification fails for optional endpoint
            const data = await apiRequest('/api/admin/terminal-text', { skipLogoutOn401: true });
            
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
            // Retry once if we get a 401 (token might not be in KV yet) and we haven't retried
            if (error.status === 401 && retryCount === 0) {
                setTimeout(() => loadTerminalText(1), 1000);
                return;
            }
            // Silently fail - terminal text is optional
            // Only log in development, not in production to avoid console noise
            if (isLocalDev()) {
                console.log('Terminal text load failed (optional):', error.message);
            }
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
