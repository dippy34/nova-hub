// Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const refreshStatsBtn = document.getElementById('refresh-stats');
    const saveGaIdBtn = document.getElementById('save-ga-id');

    // Check if already logged in
    const adminToken = Cookies.get('admin_token');
    if (adminToken) {
        verifyToken(adminToken);
    }

    // Login form handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                Cookies.set('admin_token', data.token, { expires: 7 }); // 7 days
                showDashboard(data.email);
                errorDiv.textContent = '';
            } else {
                errorDiv.textContent = data.message || 'Login failed. Please check your credentials.';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Error connecting to server. Please try again.';
            errorDiv.style.display = 'block';
            console.error('Login error:', error);
        }
    });

    // Logout handler
    logoutBtn.addEventListener('click', () => {
        Cookies.remove('admin_token');
        loginScreen.style.display = 'block';
        adminDashboard.style.display = 'none';
        document.getElementById('login-email').value = '';
        document.getElementById('login-password').value = '';
    });

    // Save GA ID handler
    saveGaIdBtn.addEventListener('click', async () => {
        const gaId = document.getElementById('ga-measurement-id').value;
        const statusDiv = document.getElementById('ga-status');
        const adminToken = Cookies.get('admin_token');

        if (!adminToken) {
            statusDiv.textContent = 'Please login first.';
            statusDiv.style.display = 'block';
            return;
        }

        try {
            const response = await fetch('/api/admin/save-ga-id', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${adminToken}`
                },
                body: JSON.stringify({ gaId })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                statusDiv.textContent = 'Google Analytics ID saved successfully.';
                statusDiv.style.color = '#00ff00';
            } else {
                statusDiv.textContent = data.message || 'Failed to save GA ID.';
                statusDiv.style.color = '#ff0000';
            }
            statusDiv.style.display = 'block';
        } catch (error) {
            statusDiv.textContent = 'Error saving GA ID. Please try again.';
            statusDiv.style.color = '#ff0000';
            statusDiv.style.display = 'block';
            console.error('Save GA ID error:', error);
        }
    });

    // Refresh stats handler
    refreshStatsBtn.addEventListener('click', () => {
        loadAnalytics();
    });

    // Verify token and show dashboard
    async function verifyToken(token) {
        try {
            const response = await fetch('/api/admin/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                showDashboard(data.email);
            } else {
                Cookies.remove('admin_token');
            }
        } catch (error) {
            console.error('Token verification error:', error);
            Cookies.remove('admin_token');
        }
    }

    // Show dashboard
    function showDashboard(email) {
        loginScreen.style.display = 'none';
        adminDashboard.style.display = 'block';
        document.getElementById('admin-email').textContent = email;
        loadAnalytics();
        loadAdminCount();
        loadGaId();
    }

    // Load analytics data
    async function loadAnalytics() {
        const adminToken = Cookies.get('admin_token');
        if (!adminToken) return;

        try {
            const response = await fetch('/api/admin/analytics', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${adminToken}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                document.getElementById('live-users').textContent = data.liveUsers || '0';
                document.getElementById('total-users').textContent = data.totalUsers || '0';
                document.getElementById('today-visits').textContent = data.todayVisits || '0';
                document.getElementById('page-views').textContent = data.pageViews || '0';
            }
        } catch (error) {
            console.error('Analytics load error:', error);
        }
    }

    // Load admin count
    async function loadAdminCount() {
        const adminToken = Cookies.get('admin_token');
        if (!adminToken) return;

        try {
            const response = await fetch('/api/admin/count', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${adminToken}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                document.getElementById('admin-count').textContent = data.count || '0';
            }
        } catch (error) {
            console.error('Admin count load error:', error);
        }
    }

    // Load GA ID
    async function loadGaId() {
        const adminToken = Cookies.get('admin_token');
        if (!adminToken) return;

        try {
            const response = await fetch('/api/admin/ga-id', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${adminToken}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success && data.gaId) {
                document.getElementById('ga-measurement-id').value = data.gaId;
            }
        } catch (error) {
            console.error('GA ID load error:', error);
        }
    }

    // Auto-refresh analytics every 30 seconds
    setInterval(() => {
        if (adminDashboard.style.display !== 'none') {
            loadAnalytics();
        }
    }, 30000);
});

