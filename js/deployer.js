// Deployer JavaScript - Admin-only GitHub repo deployer (30-min temp URLs)
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const deployerDashboard = document.getElementById('deployer-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const deployBtn = document.getElementById('deploy-btn');
    const deployResult = document.getElementById('deploy-result');
    const deployStatus = document.getElementById('deploy-status');
    const tempUrlDisplay = document.getElementById('temp-url-display');
    const copyUrlBtn = document.getElementById('copy-url-btn');
    const openUrlBtn = document.getElementById('open-url-btn');
    const countdownEl = document.getElementById('countdown');

    let countdownInterval = null;
    let currentExpiresAt = null;

    function getToken() {
        return localStorage.getItem('nova_admin_token');
    }

    function setToken(token) {
        localStorage.setItem('nova_admin_token', token);
    }

    function removeToken() {
        localStorage.removeItem('nova_admin_token');
    }

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

        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            removeToken();
            showLogin();
            throw new Error('Session expired. Please login again.');
        }

        if (!response.ok) {
            let msg = 'Request failed';
            try {
                const d = await response.json();
                msg = (d && (d.message || d.error)) || msg;
            } catch (_) {
                msg = `Request failed (${response.status} ${response.statusText})`;
            }
            throw new Error(msg);
        }

        return response.json();
    }

    function showLogin() {
        if (loginScreen) loginScreen.style.display = 'flex';
        if (deployerDashboard) deployerDashboard.style.display = 'none';
        stopCountdown();
    }

    function showDashboard() {
        if (loginScreen) loginScreen.style.display = 'none';
        if (deployerDashboard) deployerDashboard.style.display = 'block';
    }

    async function checkAuth() {
        const token = getToken();
        if (!token) {
            showLogin();
            return;
        }
        try {
            await apiRequest('/api/admin/verify');
            showDashboard();
        } catch (_) {
            showLogin();
        }
    }

    function showStatus(message, isError) {
        if (!deployStatus) return;
        deployStatus.textContent = message;
        deployStatus.className = 'status-message show ' + (isError ? 'error' : 'success');
    }

    function hideStatus() {
        if (deployStatus) {
            deployStatus.className = 'status-message';
            deployStatus.textContent = '';
        }
    }

    function formatCountdown(ms) {
        const totalSeconds = Math.max(0, Math.floor(ms / 1000));
        const m = Math.floor(totalSeconds / 60);
        const s = totalSeconds % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
    }

    function stopCountdown() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
        currentExpiresAt = null;
    }

    function startCountdown(expiresAt) {
        stopCountdown();
        currentExpiresAt = new Date(expiresAt);
        function tick() {
            const left = currentExpiresAt.getTime() - Date.now();
            if (countdownEl) countdownEl.textContent = formatCountdown(left);
            if (left <= 0) {
                stopCountdown();
                if (countdownEl) countdownEl.textContent = 'Expired';
            }
        }
        tick();
        countdownInterval = setInterval(tick, 1000);
    }

    function showResult(tempUrl, expiresAt) {
        if (tempUrlDisplay) tempUrlDisplay.value = tempUrl;
        if (openUrlBtn) {
            openUrlBtn.href = tempUrl;
            openUrlBtn.style.display = 'inline-block';
        }
        if (deployResult) {
            deployResult.classList.add('show');
        }
        startCountdown(expiresAt);
    }

    // Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const password = document.getElementById('login-password')?.value;
            const errorDiv = document.getElementById('login-error');
            try {
                const res = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });
                const data = await res.json();
                if (data.success && data.token) {
                    setToken(data.token);
                    showDashboard();
                    if (errorDiv) errorDiv.textContent = '';
                } else {
                    if (errorDiv) errorDiv.textContent = data.message || 'Login failed';
                }
            } catch (err) {
                if (errorDiv) errorDiv.textContent = 'Login failed: ' + err.message;
            }
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            removeToken();
            showLogin();
        });
    }

    // Deploy
    if (deployBtn) {
        deployBtn.addEventListener('click', async () => {
            const repoInput = document.getElementById('repo-input');
            const branchInput = document.getElementById('branch-input');
            const subpathInput = document.getElementById('subpath-input');
            const repo = (repoInput && repoInput.value) ? repoInput.value.trim() : '';
            const branch = (branchInput && branchInput.value) ? branchInput.value.trim() || 'main' : 'main';
            const subpath = (subpathInput && subpathInput.value) ? subpathInput.value.trim().replace(/^\/+|\/+$/g, '') : '';

            if (!repo) {
                showStatus('Enter a GitHub repo URL or owner/repo', true);
                return;
            }

            hideStatus();
            deployBtn.disabled = true;
            deployBtn.textContent = 'Deploying…';

            try {
                const data = await apiRequest('/api/admin/deploy', {
                    method: 'POST',
                    body: JSON.stringify({ repo, branch, subpath: subpath || undefined })
                });
                if (data.success && data.tempUrl && data.expiresAt) {
                    const base = window.location.origin;
                    const fullUrl = data.tempUrl.startsWith('http') ? data.tempUrl : base + data.tempUrl;
                    showResult(fullUrl, data.expiresAt);
                    showStatus('Deployed. Use the temp URL below. It expires in 30 minutes.', false);
                } else {
                    showStatus(data.message || 'Deploy failed', true);
                }
            } catch (err) {
                showStatus(err.message || 'Deploy failed', true);
            } finally {
                deployBtn.disabled = false;
                deployBtn.textContent = 'Deploy for 30 mins';
            }
        });
    }

    if (copyUrlBtn && tempUrlDisplay) {
        copyUrlBtn.addEventListener('click', () => {
            tempUrlDisplay.select();
            document.execCommand('copy');
            copyUrlBtn.textContent = 'Copied!';
            setTimeout(() => { copyUrlBtn.textContent = 'Copy'; }, 2000);
        });
    }

    checkAuth();
});
