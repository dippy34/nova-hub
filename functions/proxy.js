// Cloudflare Workers proxy function
// Handles /proxy route for proxying web content

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // Get the target URL from query parameter
  const targetUrl = url.searchParams.get('url');
  
  if (!targetUrl) {
    // If no URL parameter, serve a full browser UI at /proxy
    const html = `<!DOCTYPE html>
<html lang="en" class="sl-theme-dark">
<head>
  <meta charset="UTF-8" />
  <title>Scramjet Proxy - Nova Hub</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      background: #000000;
      color: #00ff00;
      font-family: 'Courier New', monospace;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .browser-toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: rgba(0, 0, 0, 0.95);
      border-bottom: 1px solid rgba(0, 255, 0, 0.3);
      flex-shrink: 0;
    }
    .toolbar-button {
      padding: 6px 12px;
      background: rgba(0, 255, 0, 0.1);
      color: #00ff00;
      border: 1px solid rgba(0, 255, 0, 0.3);
      border-radius: 4px;
      cursor: pointer;
      font-family: monospace;
      font-size: 14px;
      transition: all 0.2s;
    }
    .toolbar-button:hover {
      background: rgba(0, 255, 0, 0.2);
      border-color: #00ff00;
      box-shadow: 0 0 8px rgba(0, 255, 0, 0.3);
    }
    .toolbar-button:active {
      transform: scale(0.95);
    }
    .address-bar-container {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }
    .address-bar {
      flex: 1;
      padding: 8px 12px;
      background: #1a1a1a;
      color: #00ff00;
      border: 1px solid rgba(0, 255, 0, 0.3);
      border-radius: 4px;
      font-family: monospace;
      font-size: 14px;
      outline: none;
    }
    .address-bar:focus {
      border-color: #00ff00;
      box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
    }
    .address-bar::placeholder {
      color: #666;
    }
    .tabs-container {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 0 8px;
      background: rgba(0, 0, 0, 0.9);
      border-bottom: 1px solid rgba(0, 255, 0, 0.3);
      overflow-x: auto;
      flex-shrink: 0;
      scrollbar-width: thin;
      scrollbar-color: rgba(0, 255, 0, 0.3) transparent;
    }
    .tabs-container::-webkit-scrollbar {
      height: 4px;
    }
    .tabs-container::-webkit-scrollbar-track {
      background: transparent;
    }
    .tabs-container::-webkit-scrollbar-thumb {
      background: rgba(0, 255, 0, 0.3);
      border-radius: 2px;
    }
    .tab {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(0, 255, 0, 0.05);
      color: #888;
      border: 1px solid transparent;
      border-bottom: none;
      border-radius: 8px 8px 0 0;
      cursor: pointer;
      font-family: monospace;
      font-size: 13px;
      white-space: nowrap;
      max-width: 250px;
      min-width: 120px;
      transition: all 0.2s;
      position: relative;
    }
    .tab:hover {
      background: rgba(0, 255, 0, 0.1);
      color: #aaa;
    }
    .tab.active {
      background: rgba(0, 255, 0, 0.15);
      color: #00ff00;
      border-color: rgba(0, 255, 0, 0.3);
      border-bottom-color: #000;
      z-index: 1;
    }
    .tab-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tab-close {
      padding: 2px 6px;
      background: transparent;
      color: #666;
      border: none;
      border-radius: 3px;
      cursor: pointer;
      font-size: 16px;
      line-height: 1;
      transition: all 0.2s;
    }
    .tab-close:hover {
      background: rgba(255, 0, 0, 0.2);
      color: #ff0000;
    }
    .new-tab-button {
      padding: 8px 12px;
      background: transparent;
      color: #666;
      border: 1px dashed rgba(0, 255, 0, 0.3);
      border-radius: 4px;
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
      transition: all 0.2s;
      margin-left: 4px;
    }
    .new-tab-button:hover {
      color: #00ff00;
      border-color: #00ff00;
      background: rgba(0, 255, 0, 0.1);
    }
    .content-area {
      flex: 1;
      position: relative;
      background: #000;
      overflow: hidden;
    }
    .tab-content {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: none;
      border: none;
      background: #000;
    }
    .tab-content.active {
      display: block;
    }
    body.fullscreen .browser-toolbar,
    body.fullscreen .tabs-container {
      display: none;
    }
    body.fullscreen .content-area {
      height: 100vh;
    }
    .loading-indicator {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: #00ff00;
      font-family: monospace;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div class="browser-toolbar">
    <button class="toolbar-button" id="back-btn" title="Back">←</button>
    <button class="toolbar-button" id="forward-btn" title="Forward">→</button>
    <button class="toolbar-button" id="refresh-btn" title="Refresh">↻</button>
    <div class="address-bar-container">
      <input type="text" class="address-bar" id="address-bar" placeholder="Enter URL or search..." autocomplete="off" />
    </div>
    <button class="toolbar-button" id="go-btn" title="Go">Go</button>
    <button class="toolbar-button" id="fullscreen-btn" title="Toggle Fullscreen">⛶</button>
  </div>
  
  <div class="tabs-container" id="tabs-container">
    <!-- Tabs will be generated here -->
  </div>
  
  <div class="content-area" id="content-area">
    <!-- Tab contents (iframes) will be generated here -->
  </div>

  <script>
    let tabs = [];
    let activeTabId = null;
    let tabIdCounter = 0;
    let isFullscreen = false;

    // Initialize with a new tab
    function init() {
      createNewTab('https://www.google.com');
      setupEventListeners();
    }

    function setupEventListeners() {
      document.getElementById('go-btn').addEventListener('click', handleGo);
      document.getElementById('refresh-btn').addEventListener('click', handleRefresh);
      document.getElementById('fullscreen-btn').addEventListener('click', toggleFullscreen);
      document.getElementById('back-btn').addEventListener('click', () => {
        if (activeTabId && tabs.find(t => t.id === activeTabId)?.iframe) {
          tabs.find(t => t.id === activeTabId).iframe.contentWindow.history.back();
        }
      });
      document.getElementById('forward-btn').addEventListener('click', () => {
        if (activeTabId && tabs.find(t => t.id === activeTabId)?.iframe) {
          tabs.find(t => t.id === activeTabId).iframe.contentWindow.history.forward();
        }
      });

      const addressBar = document.getElementById('address-bar');
      addressBar.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          handleGo();
        }
      });
    }

    function createNewTab(url = null) {
      const tabId = 'tab-' + (++tabIdCounter);
      const tab = {
        id: tabId,
        url: url || 'about:blank',
        title: 'New Tab',
        iframe: null
      };
      
      tabs.push(tab);
      activeTabId = tabId;
      
      renderTabs();
      createTabIframe(tabId);
      
      if (url) {
        loadUrlInTab(tabId, url);
      } else {
        addressBar.value = '';
        addressBar.focus();
      }
    }

    function createTabIframe(tabId) {
      const contentArea = document.getElementById('content-area');
      const iframe = document.createElement('iframe');
      iframe.id = 'iframe-' + tabId;
      iframe.className = 'tab-content';
      iframe.src = 'about:blank';
      
      // Try to update title when iframe loads
      iframe.addEventListener('load', () => {
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
          const title = iframeDoc.title || 'New Tab';
          updateTabTitle(tabId, title);
        } catch (e) {
          // Cross-origin - try to extract from URL
          try {
            const url = new URL(iframe.src.split('url=')[1] || '');
            updateTabTitle(tabId, url.hostname.replace('www.', ''));
          } catch (e2) {
            updateTabTitle(tabId, 'New Tab');
          }
        }
      });
      
      contentArea.appendChild(iframe);
      
      const tab = tabs.find(t => t.id === tabId);
      if (tab) {
        tab.iframe = iframe;
      }
      
      showTab(tabId);
    }

    function renderTabs() {
      const tabsContainer = document.getElementById('tabs-container');
      tabsContainer.innerHTML = '';
      
      tabs.forEach(tab => {
        const tabEl = document.createElement('div');
        tabEl.className = 'tab' + (tab.id === activeTabId ? ' active' : '');
        tabEl.innerHTML = '<span class="tab-title">' + escapeHtml(tab.title) + '</span>' +
          '<button class="tab-close" onclick="closeTab(\\'' + tab.id + '\\', event)">×</button>';
        tabEl.addEventListener('click', (e) => {
          if (!e.target.classList.contains('tab-close')) {
            switchTab(tab.id);
          }
        });
        tabsContainer.appendChild(tabEl);
      });
      
      // Add new tab button
      const newTabBtn = document.createElement('button');
      newTabBtn.className = 'new-tab-button';
      newTabBtn.textContent = '+';
      newTabBtn.title = 'New Tab';
      newTabBtn.addEventListener('click', () => createNewTab());
      tabsContainer.appendChild(newTabBtn);
    }

    function switchTab(tabId) {
      activeTabId = tabId;
      showTab(tabId);
      renderTabs();
      
      const tab = tabs.find(t => t.id === tabId);
      if (tab) {
        document.getElementById('address-bar').value = tab.url === 'about:blank' ? '' : tab.url;
      }
    }

    function showTab(tabId) {
      tabs.forEach(tab => {
        if (tab.iframe) {
          tab.iframe.classList.toggle('active', tab.id === tabId);
        }
      });
    }

    function updateTabTitle(tabId, title) {
      const tab = tabs.find(t => t.id === tabId);
      if (tab) {
        tab.title = title || 'New Tab';
        renderTabs();
      }
    }

    function closeTab(tabId, event) {
      event.stopPropagation();
      const tabIndex = tabs.findIndex(t => t.id === tabId);
      if (tabIndex === -1) return;
      
      tabs.splice(tabIndex, 1);
      
      const iframe = document.getElementById('iframe-' + tabId);
      if (iframe) {
        iframe.remove();
      }
      
      if (activeTabId === tabId) {
        if (tabs.length > 0) {
          activeTabId = tabs[Math.max(0, tabIndex - 1)].id;
        } else {
          activeTabId = null;
          createNewTab();
        }
      }
      
      renderTabs();
      if (activeTabId) {
        showTab(activeTabId);
        const tab = tabs.find(t => t.id === activeTabId);
        if (tab) {
          document.getElementById('address-bar').value = tab.url === 'about:blank' ? '' : tab.url;
        }
      }
    }

    function handleGo() {
      const addressBar = document.getElementById('address-bar');
      const input = addressBar.value.trim();
      
      if (!input) return;
      
      let url = normalizeUrl(input);
      
      if (activeTabId) {
        loadUrlInTab(activeTabId, url);
      } else {
        createNewTab(url);
      }
    }

    function normalizeUrl(input) {
      // Check if it's already a valid URL
      try {
        const testUrl = new URL(input);
        return testUrl.href;
      } catch (e) {
        // Not a URL, check if it looks like a domain
        const domainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}(\.[a-zA-Z]{2,})?$/;
        const hasProtocol = /^https?:\/\//.test(input);
        const hasDot = input.includes('.');
        
        if (hasProtocol) {
          return input;
        } else if (hasDot && domainPattern.test(input.split('/')[0])) {
          // Looks like a domain, add https://
          return 'https://' + input;
        } else {
          // Search query - use Google
          return 'https://www.google.com/search?q=' + encodeURIComponent(input);
        }
      }
    }

    function handleRefresh() {
      if (activeTabId) {
        const tab = tabs.find(t => t.id === activeTabId);
        if (tab && tab.url && tab.url !== 'about:blank') {
          loadUrlInTab(activeTabId, tab.url);
        }
      }
    }

    function toggleFullscreen() {
      isFullscreen = !isFullscreen;
      document.body.classList.toggle('fullscreen', isFullscreen);
      
      if (isFullscreen) {
        if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen();
        } else if (document.documentElement.webkitRequestFullscreen) {
          document.documentElement.webkitRequestFullscreen();
        } else if (document.documentElement.mozRequestFullScreen) {
          document.documentElement.mozRequestFullScreen();
        } else if (document.documentElement.msRequestFullscreen) {
          document.documentElement.msRequestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
          document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
      }
    }

    function loadUrlInTab(tabId, url) {
      const tab = tabs.find(t => t.id === tabId);
      if (!tab || !tab.iframe) return;
      
      tab.url = url;
      document.getElementById('address-bar').value = url;
      
      if (url === 'about:blank') {
        tab.iframe.src = 'about:blank';
        updateTabTitle(tabId, 'New Tab');
        return;
      }
      
      // Use proxy endpoint
      const proxyUrl = '/proxy?url=' + encodeURIComponent(url);
      tab.iframe.src = proxyUrl;
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    // Handle fullscreen change events
    document.addEventListener('fullscreenchange', () => {
      isFullscreen = !!document.fullscreenElement;
      document.body.classList.toggle('fullscreen', isFullscreen);
    });
    document.addEventListener('webkitfullscreenchange', () => {
      isFullscreen = !!document.webkitFullscreenElement;
      document.body.classList.toggle('fullscreen', isFullscreen);
    });
    document.addEventListener('mozfullscreenchange', () => {
      isFullscreen = !!document.mozFullScreenElement;
      document.body.classList.toggle('fullscreen', isFullscreen);
    });
    document.addEventListener('MSFullscreenChange', () => {
      isFullscreen = !!document.msFullscreenElement;
      document.body.classList.toggle('fullscreen', isFullscreen);
    });

    // Make closeTab available globally for onclick handlers
    window.closeTab = closeTab;

    // Initialize on load
    init();
  </script>
</body>
</html>`;

    return new Response(html, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8'
      }
    });
  }
  
  try {
    // Validate URL
    const targetUrlObj = new URL(targetUrl);
    
    // Fetch the target URL
    const proxyRequest = new Request(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': targetUrl,
        'Origin': targetUrlObj.origin
      }
    });
    
    const response = await fetch(proxyRequest);
    
    // Check if it's HTML content
    const contentType = response.headers.get('content-type') || '';
    const isHtml = contentType.includes('text/html');
    
    if (!isHtml) {
      // For non-HTML content (images, CSS, JS, etc.), return as-is
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
    
    // For HTML content, rewrite URLs
    const html = await response.text();
    
    // Get the proxy base URL
    const proxyBase = `${url.origin}/proxy?url=`;
    
    // Rewrite URLs in the HTML
    let modifiedHtml = html;
    
    // Rewrite href attributes
    modifiedHtml = modifiedHtml.replace(/href=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('javascript:') || urlPath.startsWith('mailto:') || urlPath.startsWith('#') || urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `href="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite src attributes
    modifiedHtml = modifiedHtml.replace(/src=["']([^"']+)["']/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `src="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite action attributes
    modifiedHtml = modifiedHtml.replace(/action=["']([^"']+)["']/gi, (match, urlPath) => {
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `action="${proxyBase}${encodeURIComponent(absoluteUrl)}"`;
      } catch (e) {
        return match;
      }
    });
    
    // Rewrite CSS url() references
    modifiedHtml = modifiedHtml.replace(/url\(["']?([^"')]+)["']?\)/gi, (match, urlPath) => {
      if (urlPath.startsWith('data:') || urlPath.startsWith('#')) {
        return match;
      }
      try {
        const absoluteUrl = new URL(urlPath, targetUrl).href;
        return `url("${proxyBase}${encodeURIComponent(absoluteUrl)}")`;
      } catch (e) {
        return match;
      }
    });
    
    // Inject base tag to help with relative URLs
    modifiedHtml = modifiedHtml.replace(
      /<head[^>]*>/i,
      `<head><base href="${targetUrl}">`
    );
    
    // Inject proxy interceptor script before closing head or body
    const proxyScript = `
<script>
(function() {
  const PROXY_BASE = '${url.origin}/proxy?url=';
  const TARGET_ORIGIN = '${targetUrlObj.origin}';
  
  // Helper to resolve and check if URL should be proxied
  function shouldProxy(url) {
    if (!url || url === '' || url === '#') return false;
    try {
      // Resolve relative URLs
      const urlObj = new URL(url, window.location.href);
      // Don't proxy data:, javascript:, mailto:, #, or same-origin requests
      if (urlObj.protocol === 'data:' || 
          urlObj.protocol === 'javascript:' || 
          urlObj.protocol === 'mailto:' ||
          url.startsWith('#') ||
          urlObj.origin === window.location.origin) {
        return false;
      }
      return true;
    } catch (e) {
      return false;
    }
  }
  
  // Helper to proxy a URL
  function proxyUrl(url) {
    if (!url || url === '' || url === '#') return url;
    if (!shouldProxy(url)) return url;
    try {
      // Resolve relative URLs to absolute
      const absoluteUrl = new URL(url, window.location.href).href;
      return PROXY_BASE + encodeURIComponent(absoluteUrl);
    } catch (e) {
      return url;
    }
  }
  
  // Intercept fetch API
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && shouldProxy(url)) {
      args[0] = proxyUrl(url);
    } else if (url instanceof Request && shouldProxy(url.url)) {
      // Create new Request with proxied URL, preserving all options
      const proxiedUrl = proxyUrl(url.url);
      args[0] = new Request(proxiedUrl, {
        method: url.method,
        headers: url.headers,
        body: url.body,
        mode: url.mode,
        credentials: url.credentials,
        cache: url.cache,
        redirect: url.redirect,
        referrer: url.referrer,
        integrity: url.integrity
      });
    }
    return originalFetch.apply(this, args);
  };
  
  // Intercept XMLHttpRequest
  const originalXHROpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    if (shouldProxy(url)) {
      url = proxyUrl(url);
    }
    return originalXHROpen.call(this, method, url, ...rest);
  };
  
  // Intercept form submissions
  document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.tagName === 'FORM') {
      let action = form.getAttribute('action') || form.action || window.location.href;
      // Handle empty or relative actions
      if (!action || action === '#' || action === '') {
        action = window.location.href;
      }
      
      if (shouldProxy(action)) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        const formData = new FormData(form);
        const method = (form.method || 'GET').toUpperCase();
        
        if (method === 'GET') {
          const params = new URLSearchParams(formData);
          // Append form params to the original URL before proxying
          let finalUrl = action;
          if (params.toString()) {
            const separator = action.includes('?') ? '&' : '?';
            finalUrl = action + separator + params.toString();
          }
          window.location.href = proxyUrl(finalUrl);
        } else {
          // For POST and other methods, create a hidden form
          const hiddenForm = document.createElement('form');
          hiddenForm.method = form.method || 'POST';
          hiddenForm.action = proxyUrl(action);
          hiddenForm.enctype = form.enctype || 'application/x-www-form-urlencoded';
          hiddenForm.style.display = 'none';
          
          // Copy all form fields
          for (const [key, value] of formData.entries()) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = value;
            hiddenForm.appendChild(input);
          }
          
          // Copy file inputs if any
          const fileInputs = form.querySelectorAll('input[type="file"]');
          fileInputs.forEach(fileInput => {
            if (fileInput.files && fileInput.files.length > 0) {
              const newFileInput = document.createElement('input');
              newFileInput.type = 'file';
              newFileInput.name = fileInput.name;
              newFileInput.files = fileInput.files;
              hiddenForm.appendChild(newFileInput);
            }
          });
          
          document.body.appendChild(hiddenForm);
          hiddenForm.submit();
        }
        return false;
      }
    }
  }, true);
  
  // Intercept window.location changes
  let locationProxy = new Proxy(window.location, {
    set: function(target, property, value) {
      if (property === 'href' && shouldProxy(value)) {
        target.href = proxyUrl(value);
        return true;
      }
      return Reflect.set(target, property, value);
    }
  });
  
  // Intercept window.open
  const originalOpen = window.open;
  window.open = function(url, ...rest) {
    if (url && shouldProxy(url)) {
      url = proxyUrl(url);
    }
    return originalOpen.call(this, url, ...rest);
  };
  
  // Intercept anchor clicks
  document.addEventListener('click', function(e) {
    const anchor = e.target.closest('a');
    if (anchor && anchor.href && shouldProxy(anchor.href)) {
      e.preventDefault();
      window.location.href = proxyUrl(anchor.href);
    }
  }, true);
  
  // Intercept programmatic form submissions
  const originalFormSubmit = HTMLFormElement.prototype.submit;
  HTMLFormElement.prototype.submit = function() {
    const form = this;
    let action = form.getAttribute('action') || form.action || window.location.href;
    if (!action || action === '#' || action === '') {
      action = window.location.href;
    }
    
    if (shouldProxy(action)) {
      const formData = new FormData(form);
      const method = (form.method || 'GET').toUpperCase();
      
      if (method === 'GET') {
        const params = new URLSearchParams(formData);
        // Append form params to the original URL before proxying
        let finalUrl = action;
        if (params.toString()) {
          const separator = action.includes('?') ? '&' : '?';
          finalUrl = action + separator + params.toString();
        }
        window.location.href = proxyUrl(finalUrl);
      } else {
        const hiddenForm = document.createElement('form');
        hiddenForm.method = form.method || 'POST';
        hiddenForm.action = proxyUrl(action);
        hiddenForm.enctype = form.enctype || 'application/x-www-form-urlencoded';
        hiddenForm.style.display = 'none';
        
        for (const [key, value] of formData.entries()) {
          const input = document.createElement('input');
          input.type = 'hidden';
          input.name = key;
          input.value = value;
          hiddenForm.appendChild(input);
        }
        
        document.body.appendChild(hiddenForm);
        originalFormSubmit.call(hiddenForm);
      }
      return;
    }
    
    return originalFormSubmit.call(this);
  };
  
  // Intercept window.location.assign and replace
  const originalAssign = window.location.assign;
  window.location.assign = function(url) {
    return originalAssign.call(this, shouldProxy(url) ? proxyUrl(url) : url);
  };
  
  const originalReplace = window.location.replace;
  window.location.replace = function(url) {
    return originalReplace.call(this, shouldProxy(url) ? proxyUrl(url) : url);
  };
  
  console.log('Proxy interceptor loaded');
})();
</script>`;
    
    // Inject script before closing head or at start of body
    if (modifiedHtml.includes('</head>')) {
      modifiedHtml = modifiedHtml.replace('</head>', proxyScript + '</head>');
    } else if (modifiedHtml.includes('<body')) {
      modifiedHtml = modifiedHtml.replace(/<body[^>]*>/i, '$&' + proxyScript);
    } else {
      // Fallback: inject at the beginning
      modifiedHtml = proxyScript + modifiedHtml;
    }
    
    // Return the modified HTML
    return new Response(modifiedHtml, {
      status: response.status,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-cache'
      }
    });
    
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(`Proxy error: ${error.message}`, {
      status: 500,
      headers: {
        'Content-Type': 'text/plain',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
}
