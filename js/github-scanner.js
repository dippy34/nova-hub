// Git Scanner JavaScript - Admin-only Git repository scanner
document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('login-screen');
    const scannerDashboard = document.getElementById('scanner-dashboard');
    const loginForm = document.getElementById('login-form');
    const logoutBtn = document.getElementById('logout-btn');
    const searchBtn = document.getElementById('search-btn');
    
    let currentRepo = null;
    let currentPath = '';
    let currentFiles = [];

    // Authentication functions (similar to admin.js)
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

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            removeToken();
            showLogin();
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
            throw new Error(errorMessage);
        }

        return response.json();
    }

    function showLogin() {
        loginScreen.style.display = 'flex';
        scannerDashboard.style.display = 'none';
    }

    function showDashboard() {
        loginScreen.style.display = 'none';
        scannerDashboard.style.display = 'block';
    }

    // Check authentication on load
    async function checkAuth() {
        const token = getToken();
        if (!token) {
            showLogin();
            return;
        }

        try {
            await apiRequest('/api/admin/verify');
            showDashboard();
        } catch (error) {
            showLogin();
        }
    }

    // Login handler
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const password = document.getElementById('login-password').value;
            const errorDiv = document.getElementById('login-error');

            try {
                const response = await fetch('/api/admin/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ password })
                });

                const data = await response.json();

                if (data.success && data.token) {
                    setToken(data.token);
                    showDashboard();
                    errorDiv.textContent = '';
                } else {
                    errorDiv.textContent = data.message || 'Login failed';
                }
            } catch (error) {
                errorDiv.textContent = 'Login failed: ' + error.message;
            }
        });
    }

    // Logout handler
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            removeToken();
            showLogin();
            document.getElementById('login-password').value = '';
        });
    }

    // Search repository
    if (searchBtn) {
        searchBtn.addEventListener('click', async () => {
            await searchRepositories();
        });
    }

    // Handle Enter key in search input
    const repoSearchInput = document.getElementById('repo-search');
    if (repoSearchInput) {
        repoSearchInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                await searchRepositories();
            }
        });
    }

    async function searchRepositories() {
        const provider = document.getElementById('git-provider').value;
        const searchQuery = document.getElementById('repo-search').value.trim();
        const statusDiv = document.getElementById('search-status');
        const searchResultsDiv = document.getElementById('search-results');
        const searchResultsList = document.getElementById('search-results-list');

        if (!searchQuery) {
            statusDiv.textContent = 'Please enter a search query';
            statusDiv.className = 'status-message error';
            statusDiv.style.display = 'block';
            return;
        }

        searchBtn.disabled = true;
        statusDiv.textContent = 'Searching repositories...';
        statusDiv.className = 'status-message';
        statusDiv.style.display = 'block';
        searchResultsDiv.style.display = 'none';
        document.getElementById('file-browser-container').style.display = 'none';
        document.getElementById('file-content-container').style.display = 'none';
        document.getElementById('format-check-result').style.display = 'none';

        try {
            const response = await apiRequest('/api/admin/git/search', {
                method: 'POST',
                body: JSON.stringify({
                    provider,
                    query: searchQuery
                })
            });

            if (response.success && response.data.repositories) {
                const repos = response.data.repositories;
                
                if (repos.length === 0) {
                    statusDiv.textContent = 'No repositories found';
                    statusDiv.className = 'status-message error';
                    searchResultsDiv.style.display = 'none';
                } else {
                    statusDiv.textContent = `Found ${repos.length} repositories`;
                    statusDiv.className = 'status-message success';
                    renderSearchResults(repos);
                    searchResultsDiv.style.display = 'block';
                }
            }
        } catch (error) {
            statusDiv.textContent = 'Error: ' + error.message;
            statusDiv.className = 'status-message error';
            searchResultsDiv.style.display = 'none';
        } finally {
            searchBtn.disabled = false;
        }
    }

    function renderSearchResults(repos) {
        const searchResultsList = document.getElementById('search-results-list');
        
        searchResultsList.innerHTML = repos.map(repo => {
            const fullName = `${repo.owner}/${repo.name}`;
            const description = repo.description ? repo.description.substring(0, 150) + (repo.description.length > 150 ? '...' : '') : 'No description';
            const stars = repo.stars || 0;
            const updated = repo.updatedAt ? new Date(repo.updatedAt).toLocaleDateString() : '';
            
            return `
                <div class="search-results-item" data-owner="${repo.owner}" data-name="${repo.name}">
                    <strong>${fullName}</strong>
                    <p>${description}</p>
                    <div class="repo-meta">⭐ ${stars} | Updated: ${updated}</div>
                </div>
            `;
        }).join('');

        // Add click handlers
        searchResultsList.querySelectorAll('.search-results-item').forEach(item => {
            item.addEventListener('click', async () => {
                const owner = item.dataset.owner;
                const name = item.dataset.name;
                await selectRepository(owner, name);
            });
        });
    }

    async function selectRepository(owner, repoName) {
        const provider = document.getElementById('git-provider').value;
        const statusDiv = document.getElementById('search-status');
        
        statusDiv.textContent = 'Loading repository...';
        statusDiv.className = 'status-message';
        statusDiv.style.display = 'block';

        try {
            // Get repository info including default branch
            const response = await apiRequest('/api/admin/git/repo', {
                method: 'POST',
                body: JSON.stringify({
                    provider,
                    owner,
                    repo: repoName
                })
            });

            if (response.success) {
                currentRepo = {
                    provider,
                    owner: response.data.owner,
                    repo: response.data.repo,
                    branch: response.data.branch || 'main',
                    defaultBranch: response.data.defaultBranch || 'main'
                };
                currentPath = '';

                await loadDirectory('');
                statusDiv.textContent = 'Repository loaded successfully';
                statusDiv.className = 'status-message success';
                document.getElementById('file-browser-container').style.display = 'block';
                document.getElementById('search-results').style.display = 'none';
            }
        } catch (error) {
            statusDiv.textContent = 'Error loading repository: ' + error.message;
            statusDiv.className = 'status-message error';
        }
    }

    async function loadDirectory(path) {
        if (!currentRepo) return;

        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '<div class="loading">Loading files...</div>';

        try {
            const response = await apiRequest('/api/admin/git/files', {
                method: 'POST',
                body: JSON.stringify({
                    provider: currentRepo.provider,
                    owner: currentRepo.owner,
                    repo: currentRepo.repo,
                    branch: currentRepo.branch,
                    path: path || ''
                })
            });

            if (response.success) {
                currentFiles = response.data.files || [];
                currentPath = path || '';
                renderFileList(currentFiles);
                updateBreadcrumb();
            }
        } catch (error) {
            fileList.innerHTML = `<div class="status-message error">Error loading files: ${error.message}</div>`;
        }
    }

    function renderFileList(files) {
        const fileList = document.getElementById('file-list');
        
        if (files.length === 0) {
            fileList.innerHTML = '<div class="loading">No files found</div>';
            return;
        }

        // Sort: directories first, then files
        const sortedFiles = [...files].sort((a, b) => {
            if (a.type === 'dir' && b.type !== 'dir') return -1;
            if (a.type !== 'dir' && b.type === 'dir') return 1;
            return a.name.localeCompare(b.name);
        });

        fileList.innerHTML = sortedFiles.map(file => {
            const icon = file.type === 'dir' ? '📁' : '📄';
            const className = file.type === 'dir' ? 'file-item directory' : 'file-item file';
            return `
                <div class="${className}" data-name="${file.name}" data-type="${file.type}" data-path="${file.path || ''}">
                    <span>${icon}</span>
                    <span>${file.name}</span>
                </div>
            `;
        }).join('');

        // Add click handlers
        fileList.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', async () => {
                const name = item.dataset.name;
                const type = item.dataset.type;
                const filePath = item.dataset.path || (currentPath ? `${currentPath}/${name}` : name);

                if (type === 'dir') {
                    await loadDirectory(filePath);
                } else {
                    await loadFile(filePath);
                }
            });
        });
    }

    function updateBreadcrumb() {
        const breadcrumbDiv = document.getElementById('breadcrumb');
        const parts = currentPath ? currentPath.split('/').filter(p => p) : [];
        
        let html = '<span data-path="">root</span>';
        parts.forEach((part, index) => {
            const path = parts.slice(0, index + 1).join('/');
            html += ' / <span data-path="' + path + '">' + part + '</span>';
        });

        breadcrumbDiv.innerHTML = html;

        breadcrumbDiv.querySelectorAll('span').forEach(span => {
            span.addEventListener('click', async () => {
                await loadDirectory(span.dataset.path || '');
            });
        });
    }

    async function loadFile(filePath) {
        const contentContainer = document.getElementById('file-content-container');
        const fileNameDiv = document.getElementById('file-name');
        const fileContentDiv = document.getElementById('file-content');

        contentContainer.style.display = 'block';
        fileNameDiv.textContent = filePath;
        fileContentDiv.textContent = 'Loading...';

        try {
            const response = await apiRequest('/api/admin/git/file', {
                method: 'POST',
                body: JSON.stringify({
                    provider: currentRepo.provider,
                    owner: currentRepo.owner,
                    repo: currentRepo.repo,
                    branch: currentRepo.branch,
                    path: filePath
                })
            });

            if (response.success) {
                const content = response.data.content || '';
                fileContentDiv.textContent = content;
                
                // Don't auto-check format, let user click button
                document.getElementById('format-check-result').style.display = 'none';
                
                // Store content for format checking
                fileContentDiv.dataset.content = content;
            }
        } catch (error) {
            fileContentDiv.textContent = 'Error loading file: ' + error.message;
        }
    }

    function previewGame(content) {
        // Create a new window with the game content
        const previewWindow = window.open('', '_blank', 'width=1200,height=800');
        
        if (!previewWindow) {
            alert('Please allow pop-ups to preview the game');
            return;
        }
        
        // Write the HTML content to the new window
        previewWindow.document.open();
        previewWindow.document.write(content);
        previewWindow.document.close();
        
        // Focus on the new window
        previewWindow.focus();
    }

    async function checkGameFormat(content) {
        const resultDiv = document.getElementById('format-check-result');
        resultDiv.innerHTML = '<div class="loading">Checking format...</div>';
        resultDiv.style.display = 'block';

        try {
            const response = await apiRequest('/api/admin/git/check-format', {
                method: 'POST',
                body: JSON.stringify({
                    content
                })
            });

            if (response.success) {
                const { canPreview, confidence, reason } = response.data;
                const matchClass = canPreview ? '' : 'no-match';
                
                let html = `<div class="format-check-result ${matchClass}">`;
                html += `<h3>Can this game be previewed here?</h3>`;
                html += `<h2 style="margin: 15px 0; font-size: 24px;">${canPreview ? '✓ YES' : '✗ NO'}</h2>`;
                html += `<p><strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%</p>`;
                
                if (reason) {
                    html += `<p style="margin-top: 10px; color: #aaa;"><strong>Reason:</strong> ${reason}</p>`;
                }
                
                // Always show preview button (even if checker says no)
                html += `<button id="preview-game-btn" style="margin-top: 15px; padding: 10px 20px; background: ${canPreview ? '#00ff00' : '#ffaa00'}; color: #000; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 16px;">🎮 Preview Anyway</button>`;
                
                html += '</div>';
                
                resultDiv.innerHTML = html;
                
                // Add preview button handler
                const previewBtn = document.getElementById('preview-game-btn');
                if (previewBtn) {
                    previewBtn.addEventListener('click', () => {
                        previewGame(content);
                    });
                }
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="status-message error">Error checking format: ${error.message}</div>`;
        }
    }

    // Check Format button
    const checkFormatBtn = document.getElementById('check-format-btn');
    if (checkFormatBtn) {
        checkFormatBtn.addEventListener('click', async () => {
            const fileContentDiv = document.getElementById('file-content');
            const content = fileContentDiv.textContent || fileContentDiv.dataset.content || '';

            if (!content) {
                alert('No content to check');
                return;
            }

            await checkGameFormat(content);
        });
    }

    // Copy All button
    const copyAllBtn = document.getElementById('copy-all-btn');
    if (copyAllBtn) {
        copyAllBtn.addEventListener('click', () => {
            const fileContentDiv = document.getElementById('file-content');
            const content = fileContentDiv.textContent;

            navigator.clipboard.writeText(content).then(() => {
                const originalText = copyAllBtn.textContent;
                copyAllBtn.textContent = 'Copied!';
                copyAllBtn.style.background = '#00cc00';
                setTimeout(() => {
                    copyAllBtn.textContent = originalText;
                    copyAllBtn.style.background = '#00ff00';
                }, 2000);
            }).catch(err => {
                alert('Failed to copy: ' + err.message);
            });
        });
    }

    // Check Folder Format button
    const checkFolderFormatBtn = document.getElementById('check-folder-format-btn');
    if (checkFolderFormatBtn) {
        checkFolderFormatBtn.addEventListener('click', async () => {
            await checkFolderFormat();
        });
    }

    async function checkFolderFormat() {
        if (!currentRepo) {
            alert('No repository loaded');
            return;
        }

        const resultDiv = document.getElementById('format-check-result');
        resultDiv.innerHTML = '<div class="loading">Checking folder format...</div>';
        resultDiv.style.display = 'block';

        try {
            const response = await apiRequest('/api/admin/git/check-folder-format', {
                method: 'POST',
                body: JSON.stringify({
                    provider: currentRepo.provider,
                    owner: currentRepo.owner,
                    repo: currentRepo.repo,
                    branch: currentRepo.branch,
                    path: currentPath || ''
                })
            });

            if (response.success) {
                const { canPreview, confidence, reason, filePath } = response.data;
                const matchClass = canPreview ? '' : 'no-match';
                
                let html = `<div class="format-check-result ${matchClass}">`;
                html += `<h3>Can this folder/repository be previewed here?</h3>`;
                html += `<h2 style="margin: 15px 0; font-size: 24px;">${canPreview ? '✓ YES' : '✗ NO'}</h2>`;
                html += `<p><strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%</p>`;
                
                if (filePath) {
                    html += `<p><strong>Found game file:</strong> <code style="color: #00ff00;">${filePath}</code></p>`;
                }
                
                if (reason) {
                    html += `<p style="margin-top: 10px; color: #aaa;"><strong>Reason:</strong> ${reason}</p>`;
                }
                
                // Always show preview button (if we found a file path, or try to preview first HTML file found)
                let previewFilePath = filePath || null;
                
                if (filePath) {
                    html += `<button id="preview-folder-game-btn" style="margin-top: 15px; padding: 10px 20px; background: ${canPreview ? '#00ff00' : '#ffaa00'}; color: #000; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 16px;">🎮 ${canPreview ? 'Preview Game' : 'Preview Anyway'}</button>`;
                    html += `<input type="hidden" id="preview-file-path" value="${filePath}" />`;
                } else if (currentFiles && currentFiles.length > 0) {
                    // Try to find first HTML file if no file path was provided
                    const htmlFile = currentFiles.find(f => f.type === 'file' && (f.name.endsWith('.html') || f.name.endsWith('.htm')));
                    if (htmlFile) {
                        previewFilePath = htmlFile.path || (currentPath ? `${currentPath}/${htmlFile.name}` : htmlFile.name);
                        html += `<button id="preview-folder-game-btn" style="margin-top: 15px; padding: 10px 20px; background: #ffaa00; color: #000; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 16px;">🎮 Preview First HTML File</button>`;
                        html += `<input type="hidden" id="preview-file-path" value="${previewFilePath}" />`;
                    }
                }
                
                html += '</div>';
                
                resultDiv.innerHTML = html;
                
                // Add preview button handler if button was added
                const previewBtn = document.getElementById('preview-folder-game-btn');
                if (previewBtn) {
                    previewBtn.addEventListener('click', async () => {
                        const filePathToUse = document.getElementById('preview-file-path')?.value;
                        if (filePathToUse) {
                            await loadAndPreviewFile(filePathToUse);
                        } else {
                            alert('No file path found to preview');
                        }
                    });
                }
            }
        } catch (error) {
            resultDiv.innerHTML = `<div class="status-message error">Error checking folder format: ${error.message}</div>`;
        }
    }

    async function loadAndPreviewFile(filePath) {
        try {
            const response = await apiRequest('/api/admin/git/file', {
                method: 'POST',
                body: JSON.stringify({
                    provider: currentRepo.provider,
                    owner: currentRepo.owner,
                    repo: currentRepo.repo,
                    branch: currentRepo.branch,
                    path: filePath
                })
            });

            if (response.success) {
                const content = response.data.content || '';
                previewGame(content);
            }
        } catch (error) {
            alert('Error loading file for preview: ' + error.message);
        }
    }

    // Initialize
    checkAuth();
});
