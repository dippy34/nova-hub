// Admin Panel JavaScript - Client-side only (no server required)
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const adminDashboard = document.getElementById('admin-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const refreshStatsBtn = document.getElementById('refresh-stats');
    const saveGaIdBtn = document.getElementById('save-ga-id');

    // Embedded credentials (loaded from data/admin-credentials.json)
    // This allows the admin panel to work without a server
    let credentials =         [
                {
                        "email": "admin@example.com",
                        "password": "admin123",
                        "createdAt": "2024-01-01T00:00:00.000Z"
                },
                {
                        "email": "aaravharjani@icloud.com",
                        "password": "c13e1e564a9ec41ab9e14fb8d855dd0ce369a96ad894fffe1827934d0a811f35",
                        "createdAt": "2025-12-21T21:15:34.776Z"
                },
                {
                        "email": "bestboymg1@gmail.com",
                        "password": "e45ced5bb8b2d75d799d0525ff89cb03f26b400e422103e854c0b36afea0fc7f",
                        "createdAt": "2025-12-21T21:15:34.783Z"
                }
        ];

    let analytics = {
        totalUsers: 0,
        todayVisits: 0,
        pageViews: 0,
        gaMeasurementId: 'G-Y2TP19FMHZ',
        lastUpdated: null
    };

    // Try to load credentials from JSON file (if served via HTTP)
    async function loadCredentials() {
        try {
            const response = await fetch('/data/admin-credentials.json');
            if (response.ok) {
                const fileCredentials = await response.json();
                // Merge with embedded credentials, file takes priority
                const fileEmails = new Set(fileCredentials.map(c => c.email.toLowerCase()));
                credentials = [
                    ...fileCredentials,
                    ...credentials.filter(c => !fileEmails.has(c.email.toLowerCase()))
                ];
            }
        } catch (error) {
            // If fetch fails (file:// protocol), use embedded credentials
            console.log('Using embedded credentials (no server needed)');
        }
    }

    // Load analytics from JSON file initially (or use embedded default)
    async function loadAnalyticsFromFile() {
        try {
            const response = await fetch('/data/analytics.json');
            if (response.ok) {
                const fileData = await response.json();
                analytics = { ...analytics, ...fileData };
                saveAnalyticsToStorage();
            }
        } catch (error) {
            // If fetch fails, use localStorage or default values
            console.log('Analytics file not accessible, using localStorage or defaults');
        }
    }

    // Load analytics from localStorage
    function loadAnalyticsFromStorage() {
        const stored = localStorage.getItem('nova_admin_analytics');
        if (stored) {
            analytics = { ...analytics, ...JSON.parse(stored) };
        }
    }

    // Save analytics to localStorage
    function saveAnalyticsToStorage() {
        localStorage.setItem('nova_admin_analytics', JSON.stringify(analytics));
    }

    // SHA-256 hash function for browser
    async function hashPassword(password) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // Initialize
    async function init() {
        await loadCredentials();
        await loadAnalyticsFromFile();
        loadAnalyticsFromStorage();
        
        const loggedInEmail = localStorage.getItem('nova_admin_email');
        if (loggedInEmail) {
            showDashboard(loggedInEmail);
        }
    }
    
    init();

    // Login form handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const errorDiv = document.getElementById('login-error');

        if (credentials.length === 0) {
            errorDiv.textContent = 'No admin accounts found. Please add admin accounts using the import script.';
            errorDiv.style.display = 'block';
            return;
        }

        try {
            const hashedPassword = await hashPassword(password);
            const admin = credentials.find(cred => 
                cred.email.toLowerCase() === email.toLowerCase() && 
                cred.password === hashedPassword
            );

            if (!admin) {
                // Check if password is stored as plain text (for initial setup)
                const adminPlain = credentials.find(cred => 
                    cred.email.toLowerCase() === email.toLowerCase() && 
                    cred.password === password
                );
                
                if (adminPlain) {
                    // Update to hashed password (but we can't write to file client-side)
                    // Just allow login
                    localStorage.setItem('nova_admin_email', adminPlain.email);
                    showDashboard(adminPlain.email);
                    errorDiv.textContent = '';
                    return;
                }
                
                errorDiv.textContent = 'Invalid credentials. Please check your email and password.';
                errorDiv.style.display = 'block';
                return;
            }

            localStorage.setItem('nova_admin_email', admin.email);
            showDashboard(admin.email);
            errorDiv.textContent = '';
        } catch (error) {
            errorDiv.textContent = 'Error during login. Please try again.';
            errorDiv.style.display = 'block';
            console.error('Login error:', error);
        }
    });

    // Logout handler
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('nova_admin_email');
        loginScreen.style.display = 'block';
        adminDashboard.style.display = 'none';
        document.getElementById('login-email').value = '';
        document.getElementById('login-password').value = '';
    });

    // Save GA ID handler
    saveGaIdBtn.addEventListener('click', () => {
        const gaId = document.getElementById('ga-measurement-id').value;
        const statusDiv = document.getElementById('ga-status');
        
        if (!localStorage.getItem('nova_admin_email')) {
            statusDiv.textContent = 'Please login first.';
            statusDiv.style.display = 'block';
            return;
        }

        analytics.gaMeasurementId = gaId || '';
        analytics.lastUpdated = new Date().toISOString();
        saveAnalyticsToStorage();
        
        statusDiv.textContent = 'Google Analytics ID saved successfully.';
        statusDiv.style.color = '#00ff00';
        statusDiv.style.display = 'block';
    });

    // Refresh stats handler
    refreshStatsBtn.addEventListener('click', () => {
        loadAnalytics();
    });

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
    function loadAnalytics() {
        loadAnalyticsFromStorage();
        
        // For Google Analytics, you'd need to integrate with GA API
        // For now, just show stored values
        document.getElementById('live-users').textContent = '0'; // GA integration needed
        document.getElementById('total-users').textContent = analytics.totalUsers || '0';
        document.getElementById('today-visits').textContent = analytics.todayVisits || '0';
        document.getElementById('page-views').textContent = analytics.pageViews || '0';
    }

    // Load admin count
    function loadAdminCount() {
        document.getElementById('admin-count').textContent = credentials.length || '0';
    }

    // Load GA ID
    function loadGaId() {
        if (analytics.gaMeasurementId) {
            document.getElementById('ga-measurement-id').value = analytics.gaMeasurementId;
        }
    }

    // Auto-refresh analytics every 30 seconds
    setInterval(() => {
        if (adminDashboard.style.display !== 'none') {
            loadAnalytics();
        }
    }, 30000);
});
