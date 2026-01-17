// Load environment variables from .env file
require('dotenv').config();

const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);


// Google APIs - optional, only load if service account file exists
let google;
try {
  if (fs.existsSync(path.join(__dirname, 'ga-service-account.json'))) {
    google = require('googleapis').google;
  }
} catch (error) {
  console.warn('Google APIs not available. Install with: npm install googleapis');
}

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API routes (before static file serving)
// Submit a suggestion or bug report
app.post('/api/submit-suggestion', (req, res) => {
  try {
    const { type, title, description, email, steps } = req.body;
    
    // Get IP address from request - try multiple sources
    let ip = req.headers['x-forwarded-for'] || 
             req.headers['x-real-ip'] || 
             req.ip ||
             (req.connection && req.connection.remoteAddress) || 
             (req.socket && req.socket.remoteAddress) ||
             (req.connection && req.connection.socket && req.connection.socket.remoteAddress) ||
             null;
    
    // If still no IP, try req.socket directly
    if (!ip && req.socket && req.socket.remoteAddress) {
      ip = req.socket.remoteAddress;
    }
    
    // If still no IP and we have req.connection, try it
    if (!ip && req.connection && req.connection.remoteAddress) {
      ip = req.connection.remoteAddress;
    }
    
    // Extract the first IP if it's a comma-separated list (from proxy)
    if (ip) {
      ip = String(ip).split(',')[0].trim();
      
      // Remove IPv6 prefix if present (::ffff:192.168.1.1 -> 192.168.1.1)
      if (ip.startsWith('::ffff:')) {
        ip = ip.substring(7);
      }
      
      // Handle IPv6 localhost (::1 -> 127.0.0.1)
      if (ip === '::1' || ip === '::ffff:127.0.0.1') {
        ip = '127.0.0.1';
      }
    }
    
    // Default to localhost IP if nothing found (for localhost requests)
    const clientIp = ip || '127.0.0.1';
    
    console.log('Received suggestion submission:', { type, title, description, email, ip: clientIp });
    
    if (!type || !title) {
      return res.status(400).json({ success: false, message: 'Type and title are required' });
    }

    const suggestionsPath = path.join(__dirname, 'data', 'suggestions.json');
    let suggestions;
    
    try {
      suggestions = readJsonFile(suggestionsPath);
    } catch (error) {
      console.error('Error reading suggestions file:', error);
      // Initialize empty structure if file doesn't exist or is invalid
      suggestions = {
        gameSuggestions: [],
        featureSuggestions: [],
        bugReports: []
      };
    }

    // Ensure arrays exist
    if (!suggestions.gameSuggestions) suggestions.gameSuggestions = [];
    if (!suggestions.featureSuggestions) suggestions.featureSuggestions = [];
    if (!suggestions.bugReports) suggestions.bugReports = [];

    const newSuggestion = {
      title: title,
      description: description || '',
      email: email || '',
      ip: clientIp,
      date: new Date().toISOString()
    };

    if (steps) {
      newSuggestion.steps = steps;
    }

    if (type === 'game') {
      suggestions.gameSuggestions.push(newSuggestion);
    } else if (type === 'feature') {
      suggestions.featureSuggestions.push(newSuggestion);
    } else if (type === 'bug') {
      suggestions.bugReports.push(newSuggestion);
    } else {
      return res.status(400).json({ success: false, message: 'Invalid type. Must be game, feature, or bug' });
    }

    try {
      if (writeJsonFile(suggestionsPath, suggestions)) {
        console.log('Successfully saved suggestion from IP:', clientIp);
        res.json({ success: true, message: 'Thank you! Your message has been sent successfully.' });
      } else {
        console.error('Failed to write suggestions file');
        res.status(500).json({ success: false, message: 'Failed to save suggestion' });
      }
    } catch (error) {
      console.error('Error writing suggestions file:', error);
      res.status(500).json({ success: false, message: 'Failed to save suggestion: ' + error.message });
    }
  } catch (error) {
    console.error('Error in submit-suggestion endpoint:', error);
    res.status(500).json({ success: false, message: 'Internal server error: ' + error.message });
  }
});

// Static file serving (must be after API routes)
// Configure to pass through to next handler if file doesn't exist
app.use(express.static(__dirname, { fallthrough: true }));

app.get('/projects', (req, res) => {
  res.sendFile(path.join(__dirname, 'projects.html'));
});

app.get('/settings', (req, res) => {
  res.sendFile(path.join(__dirname, 'settings.html'));
});

app.get('/about', (req, res) => {
  res.sendFile(path.join(__dirname, 'about.html'));
});

app.get('/transfer', (req, res) => {
  res.sendFile(path.join(__dirname, 'transfer.html'));
});

app.get('/suggest', (req, res) => {
  res.sendFile(path.join(__dirname, 'suggest.html'));
});

app.get('/ad', (req, res) => {
  res.sendFile(path.join(__dirname, 'ad.html'));
});

app.get('/blank', (req, res) => {
  res.sendFile(path.join(__dirname, 'blank.html'));
});
app.get('/backgrounds', (req, res) => {
  res.sendFile(path.join(__dirname, 'backgrounds.html'));
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/admin-git-scanner', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin-git-scanner.html'));
});

app.get('/admin-git-scanner.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'admin-git-scanner.html'));
});

// Helper functions
function readJsonFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return {};
    }
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading JSON file:', filePath, error);
    return {};
  }
}

function writeJsonFile(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Error writing file:', error);
    return false;
  }
}

function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

// Programmatic credential import function
// Usage: require('./index.js').importAdminCredentials([{email: 'test@example.com', password: 'pass123'}])
function importAdminCredentials(credentials) {
  if (!Array.isArray(credentials)) {
    throw new Error('Credentials must be an array');
  }

  const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
  const existing = readJsonFile(credentialsPath);
  const existingEmails = new Set(existing.map(c => c.email.toLowerCase()));
  
  let added = 0;
  let skipped = 0;

  credentials.forEach(cred => {
    if (!cred.email || !cred.password) {
      console.warn('⚠ Skipped invalid credential (missing email or password)');
      skipped++;
      return;
    }

    const email = cred.email.toLowerCase();
    
    if (existingEmails.has(email)) {
      console.log(`⚠ Skipped ${cred.email} (already exists)`);
      skipped++;
      return;
    }

    existing.push({
      email: cred.email,
      password: hashPassword(cred.password),
      createdAt: new Date().toISOString()
    });
    
    existingEmails.add(email);
    console.log(`✓ Added ${cred.email}`);
    added++;
  });

  if (writeJsonFile(credentialsPath, existing)) {
    console.log(`\n📊 Summary: ${added} added, ${skipped} skipped, ${existing.length} total`);
    return { success: true, added, skipped, total: existing.length };
  } else {
    return { success: false, message: 'Failed to write credentials file' };
  }
}

// Export for programmatic use (only when required as module, not when run directly)
if (require.main !== module) {
  module.exports = { importAdminCredentials, hashPassword, readJsonFile, writeJsonFile };
}

function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

// Simple token storage (in production, use Redis or database)
const activeTokens = {};

// Middleware to verify admin token
function verifyAdminToken(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: 'No token provided' });
  }

  const token = authHeader.substring(7);
  const adminData = activeTokens[token];

  if (!adminData || !adminData.authenticated) {
    return res.status(401).json({ success: false, message: 'Invalid token' });
  }

  next();
}

// Admin API Routes
app.post('/api/admin/login', (req, res) => {
  try {
    const { password } = req.body;

    if (!password) {
      return res.status(400).json({ success: false, message: 'Password required' });
    }

    // Get stored password hash, or initialize with default password
    const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
    let credentials = readJsonFile(credentialsPath);
    
    // Migrate from old array format to new object format
    if (Array.isArray(credentials)) {
      // Old format - migrate to new format with default password
      const defaultPassword = 'nova_admin_aarav_matthew';
      const hashedDefaultPassword = hashPassword(defaultPassword);
      credentials = { adminPassword: hashedDefaultPassword };
      fs.writeFileSync(credentialsPath, JSON.stringify(credentials, null, 2));
    }
    
    // If no password is stored, initialize with default password
    if (!credentials || !credentials.adminPassword) {
      const defaultPassword = 'nova_admin_aarav_matthew';
      const hashedDefaultPassword = hashPassword(defaultPassword);
      credentials = { adminPassword: hashedDefaultPassword };
      fs.writeFileSync(credentialsPath, JSON.stringify(credentials, null, 2));
    }

    const hashedPassword = hashPassword(password);

    if (hashedPassword !== credentials.adminPassword) {
      return res.status(401).json({ success: false, message: 'Invalid password' });
    }

    const token = generateToken();
    activeTokens[token] = { authenticated: true };
    res.json({ success: true, token });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ success: false, message: 'Server error during login' });
  }
});

app.get('/api/admin/verify', verifyAdminToken, (req, res) => {
  res.json({ success: true });
});

// Change admin password
app.post('/api/admin/change-password', verifyAdminToken, (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;

    if (!currentPassword || !newPassword) {
      return res.status(400).json({ success: false, message: 'Current password and new password are required' });
    }

    if (newPassword.length < 8) {
      return res.status(400).json({ success: false, message: 'New password must be at least 8 characters long' });
    }

    // Get stored password hash
    const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
    let credentials = readJsonFile(credentialsPath);
    
    // If no password is stored, initialize with default password
    if (!credentials || !credentials.adminPassword) {
      const defaultPassword = 'nova_admin_aarav_matthew';
      const hashedDefaultPassword = hashPassword(defaultPassword);
      credentials = { adminPassword: hashedDefaultPassword };
    }

    // Verify current password
    const hashedCurrentPassword = hashPassword(currentPassword);
    if (hashedCurrentPassword !== credentials.adminPassword) {
      return res.status(401).json({ success: false, message: 'Current password is incorrect' });
    }

    // Set new password
    const hashedNewPassword = hashPassword(newPassword);
    credentials.adminPassword = hashedNewPassword;
    writeJsonFile(credentialsPath, credentials);

    res.json({ success: true, message: 'Password changed successfully' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ success: false, message: 'Internal server error' });
  }
});


// Commit changes to git
app.post('/api/admin/commit-changes', verifyAdminToken, async (req, res) => {
  try {
    const { message } = req.body;
    const commitMessage = message || 'Add new admin account';

    // Stage the admin-credentials.json file
    try {
      await execPromise(`cd ${__dirname} && git add data/admin-credentials.json`);
      
      // Commit the changes
      await execPromise(`cd ${__dirname} && git commit -m "${commitMessage.replace(/"/g, '\\"')}"`);
      
      res.json({ success: true, message: 'Changes committed successfully' });
    } catch (gitError) {
      console.error('Git commit error:', gitError);
      // Check if there are no changes to commit
      if (gitError.message && gitError.message.includes('nothing to commit')) {
        return res.status(400).json({ success: false, message: 'No changes to commit' });
      }
      return res.status(500).json({ success: false, message: 'Failed to commit changes: ' + gitError.message });
    }
  } catch (error) {
    console.error('Commit changes error:', error);
    res.status(500).json({ success: false, message: 'Server error: ' + error.message });
  }
});

app.get('/api/admin/analytics', verifyAdminToken, async (req, res) => {
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);

  let liveUsers = 0;
  let todayVisits = 0;
  let totalPageViews = 0;

  // Fetch from Google Analytics if configured
  if (analytics.gaMeasurementId && google) {
    try {
      const serviceAccountPath = path.join(__dirname, 'ga-service-account.json');
      
      if (fs.existsSync(serviceAccountPath)) {
        const auth = new google.auth.GoogleAuth({
          keyFile: serviceAccountPath,
          scopes: ['https://www.googleapis.com/auth/analytics.readonly']
        });

        const analyticsData = google.analyticsdata('v1beta');
        const propertyId = analytics.gaMeasurementId.replace('G-', '');

        // Get real-time active users
        try {
          const realtimeResponse = await analyticsData.properties.runRealtimeReport({
            auth: auth,
            property: `properties/${propertyId}`,
            requestBody: {
              metrics: [{ name: 'activeUsers' }]
            }
          });
          liveUsers = parseInt(realtimeResponse.data.rows?.[0]?.metricValues?.[0]?.value || 0);
        } catch (error) {
          console.error('GA Realtime API Error:', error.message);
        }

        // Get today's visits and total page views
        try {
          const today = new Date();
          const startDate = today.toISOString().split('T')[0];
          const endDate = startDate;

          const reportResponse = await analyticsData.properties.runReport({
            auth: auth,
            property: `properties/${propertyId}`,
            requestBody: {
              dateRanges: [{ startDate, endDate }],
              metrics: [
                { name: 'sessions' },
                { name: 'screenPageViews' }
              ]
            }
          });

          if (reportResponse.data.rows && reportResponse.data.rows.length > 0) {
            todayVisits = parseInt(reportResponse.data.rows[0].metricValues?.[0]?.value || 0);
            totalPageViews = parseInt(reportResponse.data.rows[0].metricValues?.[1]?.value || 0);
          }
        } catch (error) {
          console.error('GA Report API Error:', error.message);
        }
      }
    } catch (error) {
      console.error('Google Analytics API Error:', error.message);
    }
  }

  // Use GA data if available, otherwise use local tracking
  res.json({
    success: true,
    liveUsers: liveUsers,
    totalUsers: analytics.totalUsers || 0,
    todayVisits: todayVisits || analytics.todayVisits || 0,
    pageViews: totalPageViews || analytics.pageViews || 0
  });
});

app.get('/api/admin/ga-id', verifyAdminToken, (req, res) => {
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);
  res.json({ success: true, gaId: analytics.gaMeasurementId || '' });
});

app.post('/api/admin/save-ga-id', verifyAdminToken, (req, res) => {
  const { gaId } = req.body;
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);

  analytics.gaMeasurementId = gaId || '';
  analytics.lastUpdated = new Date().toISOString();

  if (writeJsonFile(analyticsPath, analytics)) {
    res.json({ success: true });
  } else {
    res.status(500).json({ success: false, message: 'Failed to save GA ID' });
  }
});

// Terminal text endpoints
app.get('/api/terminal-text', (req, res) => {
  const terminalTextPath = path.join(__dirname, 'data', 'terminal-text.json');
  const terminalText = readJsonFile(terminalTextPath);
  
  // Default values if file doesn't exist
  const defaultData = {
    welcomeLines: ['Welcome to Nova Hub', 'Your ultimate gaming destination'],
    statusText: 'If you see this, it loaded.'
  };
  
  const data = {
    welcomeLines: terminalText.welcomeLines || defaultData.welcomeLines,
    statusText: terminalText.statusText || defaultData.statusText
  };
  
  res.json({ success: true, data });
});

app.get('/api/admin/terminal-text', verifyAdminToken, (req, res) => {
  const terminalTextPath = path.join(__dirname, 'data', 'terminal-text.json');
  const terminalText = readJsonFile(terminalTextPath);
  
  // Default values if file doesn't exist
  const defaultData = {
    welcomeLines: ['Welcome to Nova Hub', 'Your ultimate gaming destination'],
    statusText: 'If you see this, it loaded.'
  };
  
  const data = {
    welcomeLines: terminalText.welcomeLines || defaultData.welcomeLines,
    statusText: terminalText.statusText || defaultData.statusText
  };
  
  res.json({ success: true, data });
});

app.post('/api/admin/save-terminal-text', verifyAdminToken, (req, res) => {
  try {
    const { welcomeLines, statusText } = req.body;
    const terminalTextPath = path.join(__dirname, 'data', 'terminal-text.json');
    
    // Parse welcome lines if it's a string
    let parsedWelcomeLines = welcomeLines;
    if (typeof welcomeLines === 'string') {
      parsedWelcomeLines = welcomeLines.split('\n').filter(line => line.trim() !== '');
    }
    
    const terminalText = {
      welcomeLines: parsedWelcomeLines || ['Welcome to Nova Hub', 'Your ultimate gaming destination'],
      statusText: statusText || 'If you see this, it loaded.',
      lastUpdated: new Date().toISOString()
    };
    
    if (writeJsonFile(terminalTextPath, terminalText)) {
      res.json({ success: true, message: 'Terminal text saved successfully' });
    } else {
      res.status(500).json({ success: false, message: 'Failed to save terminal text' });
    }
  } catch (error) {
    console.error('Error saving terminal text:', error);
    res.status(500).json({ success: false, message: 'Error saving terminal text: ' + error.message });
  }
});

// Get all suggestions and bug reports
app.get('/api/admin/suggestions', verifyAdminToken, (req, res) => {
  const suggestionsPath = path.join(__dirname, 'data', 'suggestions.json');
  const suggestions = readJsonFile(suggestionsPath);
  res.json({ success: true, data: suggestions });
});

// Delete a suggestion or bug report
app.post('/api/admin/delete-suggestion', verifyAdminToken, (req, res) => {
  try {
    const { type, index } = req.body;
    
    console.log('Delete request received:', { type, index, indexType: typeof index });
    
    if (!type || typeof index === 'undefined' || index === null) {
      return res.status(400).json({ success: false, message: 'Type and index are required' });
    }

    // Convert index to number if it's a string
    const indexNum = parseInt(index, 10);
    if (isNaN(indexNum)) {
      return res.status(400).json({ success: false, message: 'Index must be a valid number' });
    }

    const suggestionsPath = path.join(__dirname, 'data', 'suggestions.json');
    let suggestions;
    
    try {
      suggestions = readJsonFile(suggestionsPath);
      // If readJsonFile returns an empty array, initialize proper structure
      if (Array.isArray(suggestions)) {
        suggestions = {
          gameSuggestions: [],
          featureSuggestions: [],
          bugReports: []
        };
      }
    } catch (error) {
      console.error('Error reading suggestions file:', error);
      return res.status(500).json({ success: false, message: 'Failed to read suggestions file: ' + error.message });
    }

    // Ensure arrays exist
    if (!suggestions.gameSuggestions) suggestions.gameSuggestions = [];
    if (!suggestions.featureSuggestions) suggestions.featureSuggestions = [];
    if (!suggestions.bugReports) suggestions.bugReports = [];

    let targetArray;
    if (type === 'game') {
      targetArray = suggestions.gameSuggestions;
    } else if (type === 'feature') {
      targetArray = suggestions.featureSuggestions;
    } else if (type === 'bug') {
      targetArray = suggestions.bugReports;
    } else {
      return res.status(400).json({ success: false, message: 'Invalid type. Must be game, feature, or bug' });
    }

    console.log(`Target array length: ${targetArray.length}, index: ${indexNum}`);

    if (indexNum < 0 || indexNum >= targetArray.length) {
      return res.status(400).json({ success: false, message: `Invalid index: ${indexNum}. Array length is ${targetArray.length}` });
    }

    // Remove the item at the specified index
    const deleted = targetArray.splice(indexNum, 1);
    console.log(`Deleted item:`, deleted);

    try {
      if (writeJsonFile(suggestionsPath, suggestions)) {
        console.log(`Successfully deleted ${type} suggestion at index ${indexNum}`);
        res.json({ success: true, message: 'Suggestion deleted successfully' });
      } else {
        console.error('Failed to write suggestions file');
        res.status(500).json({ success: false, message: 'Failed to save changes' });
      }
    } catch (error) {
      console.error('Error writing suggestions file:', error);
      res.status(500).json({ success: false, message: 'Failed to save changes: ' + error.message });
    }
  } catch (error) {
    console.error('Error in delete-suggestion endpoint:', error);
    res.status(500).json({ success: false, message: 'Internal server error: ' + error.message });
  }
});

// Track page views (call this from your main site)
app.post('/api/track-visit', (req, res) => {
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);

  const today = new Date().toDateString();
  const lastUpdate = analytics.lastUpdated ? new Date(analytics.lastUpdated).toDateString() : null;

  // Reset today's visits if it's a new day
  if (lastUpdate !== today) {
    analytics.todayVisits = 0;
  }

  analytics.todayVisits = (analytics.todayVisits || 0) + 1;
  analytics.pageViews = (analytics.pageViews || 0) + 1;
  analytics.totalUsers = Math.max(analytics.totalUsers || 0, analytics.todayVisits);
  analytics.lastUpdated = new Date().toISOString();

  writeJsonFile(analyticsPath, analytics);
  res.json({ success: true });
});

// Git Scanner API Endpoints

// Helper function to parse GitHub/GitLab repo URL
function parseRepoUrl(repoUrl, provider) {
  // Remove protocol and www
  let cleanUrl = repoUrl.replace(/^https?:\/\//, '').replace(/^www\./, '');
  
  // Remove .git suffix
  cleanUrl = cleanUrl.replace(/\.git$/, '');
  
  // Handle GitHub URLs
  if (provider === 'github') {
    // github.com/owner/repo or gitlab.com/owner/repo
    const githubMatch = cleanUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
    if (githubMatch) {
      return { owner: githubMatch[1], repo: githubMatch[2] };
    }
    
    // Try as owner/repo format
    const slashMatch = cleanUrl.match(/^([^\/]+)\/([^\/]+)$/);
    if (slashMatch) {
      return { owner: slashMatch[1], repo: slashMatch[2] };
    }
  }
  
  // Handle GitLab URLs
  if (provider === 'gitlab') {
    const gitlabMatch = cleanUrl.match(/gitlab\.com\/([^\/]+)\/([^\/]+)/);
    if (gitlabMatch) {
      return { owner: gitlabMatch[1], repo: gitlabMatch[2] };
    }
    
    // Try as owner/repo format
    const slashMatch = cleanUrl.match(/^([^\/]+)\/([^\/]+)$/);
    if (slashMatch) {
      return { owner: slashMatch[1], repo: slashMatch[2] };
    }
  }
  
  return null;
}

// Search repositories
app.post('/api/admin/git/search', verifyAdminToken, async (req, res) => {
  try {
    const { provider, query } = req.body;
    
    if (!provider || !query) {
      return res.status(400).json({ success: false, message: 'Provider and search query are required' });
    }
    
    const token = provider === 'github' ? process.env.GITHUB_TOKEN : process.env.GITLAB_TOKEN;
    const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
    
    let repositories = [];
    
    if (provider === 'github') {
      const apiUrl = `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}&per_page=30&sort=stars`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      repositories = (data.items || []).map(item => ({
        owner: item.owner.login,
        name: item.name,
        fullName: item.full_name,
        description: item.description || '',
        stars: item.stargazers_count || 0,
        updatedAt: item.updated_at,
        defaultBranch: item.default_branch || 'main'
      }));
    } else if (provider === 'gitlab') {
      const apiUrl = `https://gitlab.com/api/v4/projects?search=${encodeURIComponent(query)}&per_page=30&order_by=updated_desc`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitLab API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      repositories = (data || []).map(item => {
        const pathParts = item.path_with_namespace.split('/');
        return {
          owner: pathParts[0],
          name: item.name,
          fullName: item.path_with_namespace,
          description: item.description || '',
          stars: item.star_count || 0,
          updatedAt: item.last_activity_at,
          defaultBranch: item.default_branch || 'main'
        };
      });
    }
    
    res.json({
      success: true,
      data: {
        repositories,
        total: repositories.length
      }
    });
  } catch (error) {
    console.error('Error searching repositories:', error);
    res.status(500).json({ success: false, message: 'Failed to search repositories: ' + error.message });
  }
});

// Fetch repository info
app.post('/api/admin/git/repo', verifyAdminToken, async (req, res) => {
  try {
    const { provider, repoUrl, owner, repo } = req.body;
    
    if (!provider) {
      return res.status(400).json({ success: false, message: 'Provider is required' });
    }
    
    let repoInfo;
    
    // If owner and repo are provided directly, use them
    if (owner && repo) {
      repoInfo = { owner, repo };
    } else if (repoUrl) {
      // Otherwise parse from URL
      repoInfo = parseRepoUrl(repoUrl, provider);
      if (!repoInfo) {
        return res.status(400).json({ success: false, message: 'Invalid repository URL format or missing owner/repo' });
      }
    } else {
      return res.status(400).json({ success: false, message: 'Either repoUrl or owner/repo is required' });
    }
    
    const token = provider === 'github' ? process.env.GITHUB_TOKEN : process.env.GITLAB_TOKEN;
    const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
    
    let defaultBranch = 'main';
    
    // Fetch default branch from API
    try {
      if (provider === 'github') {
        const apiUrl = `https://api.github.com/repos/${repoInfo.owner}/${repoInfo.repo}`;
        const response = await fetch(apiUrl, { headers: authHeader });
        if (response.ok) {
          const data = await response.json();
          defaultBranch = data.default_branch || 'main';
        }
      } else if (provider === 'gitlab') {
        const apiUrl = `https://gitlab.com/api/v4/projects/${encodeURIComponent(repoInfo.owner + '/' + repoInfo.repo)}`;
        const response = await fetch(apiUrl, { headers: authHeader });
        if (response.ok) {
          const data = await response.json();
          defaultBranch = data.default_branch || 'main';
        }
      }
    } catch (error) {
      console.warn('Could not fetch default branch, using fallback:', error.message);
    }
    
    res.json({
      success: true,
      data: {
        owner: repoInfo.owner,
        repo: repoInfo.repo,
        branch: defaultBranch,
        defaultBranch: defaultBranch
      }
    });
  } catch (error) {
    console.error('Error fetching repo info:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch repository: ' + error.message });
  }
});

// List files in repository
app.post('/api/admin/git/files', verifyAdminToken, async (req, res) => {
  try {
    const { provider, owner, repo, branch, path: filePath } = req.body;
    
    if (!provider || !owner || !repo || !branch) {
      return res.status(400).json({ success: false, message: 'Provider, owner, repo, and branch are required' });
    }
    
    const token = provider === 'github' ? process.env.GITHUB_TOKEN : process.env.GITLAB_TOKEN;
    const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
    
    let files = [];
    
    if (provider === 'github') {
      const apiPath = filePath ? `contents/${filePath}` : 'contents';
      const apiUrl = `https://api.github.com/repos/${owner}/${repo}/${apiPath}?ref=${branch}`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      files = Array.isArray(data) ? data : [data];
      
      files = files.map(file => ({
        name: file.name,
        type: file.type === 'dir' ? 'dir' : 'file',
        path: file.path,
        size: file.size || 0
      }));
    } else if (provider === 'gitlab') {
      const projectId = encodeURIComponent(`${owner}/${repo}`);
      const apiPath = filePath ? `tree?path=${encodeURIComponent(filePath)}&ref=${branch}` : `tree?ref=${branch}`;
      const apiUrl = `https://gitlab.com/api/v4/projects/${projectId}/repository/${apiPath}`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitLab API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      files = Array.isArray(data) ? data : [];
      
      files = files.map(file => ({
        name: file.name,
        type: file.type === 'tree' ? 'dir' : 'file',
        path: file.path,
        size: file.size || 0
      }));
    }
    
    res.json({
      success: true,
      data: {
        files,
        path: filePath || ''
      }
    });
  } catch (error) {
    console.error('Error fetching files:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch files: ' + error.message });
  }
});

// Get file content
app.post('/api/admin/git/file', verifyAdminToken, async (req, res) => {
  try {
    const { provider, owner, repo, branch, path: filePath } = req.body;
    
    if (!provider || !owner || !repo || !branch || !filePath) {
      return res.status(400).json({ success: false, message: 'Provider, owner, repo, branch, and path are required' });
    }
    
    const token = provider === 'github' ? process.env.GITHUB_TOKEN : process.env.GITLAB_TOKEN;
    const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
    
    let content = '';
    
    if (provider === 'github') {
      const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${filePath}?ref=${branch}`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.encoding === 'base64') {
        content = Buffer.from(data.content, 'base64').toString('utf-8');
      } else {
        content = data.content || '';
      }
    } else if (provider === 'gitlab') {
      const projectId = encodeURIComponent(`${owner}/${repo}`);
      const apiUrl = `https://gitlab.com/api/v4/projects/${projectId}/repository/files/${encodeURIComponent(filePath)}/raw?ref=${branch}`;
      const response = await fetch(apiUrl, { headers: authHeader });
      
      if (!response.ok) {
        throw new Error(`GitLab API error: ${response.status} ${response.statusText}`);
      }
      
      content = await response.text();
    }
    
    res.json({
      success: true,
      data: {
        content,
        path: filePath
      }
    });
  } catch (error) {
    console.error('Error fetching file:', error);
    res.status(500).json({ success: false, message: 'Failed to fetch file: ' + error.message });
  }
});

// Check game format using AI
app.post('/api/admin/git/check-format', verifyAdminToken, async (req, res) => {
  try {
    const { content, repoOwner, repoName } = req.body;
    
    if (!content) {
      return res.status(400).json({ success: false, message: 'Content is required' });
    }
    
    const openaiKey = process.env.OPENAI_API_KEY;
    if (!openaiKey) {
      return res.status(500).json({ success: false, message: 'OpenAI API key not configured' });
    }
    
    // Build prompt for OpenAI - simple yes/no question
    const prompt = `Analyze this HTML/JavaScript code and determine: Can this game be previewed/played directly in a web browser right here?

Consider:
- Does it contain complete game code (HTML, CSS, JavaScript)?
- Can it run standalone without external server requirements?
- Is it a playable game interface?

Here's the code to check:

${content.substring(0, 10000)}${content.length > 10000 ? '... (truncated)' : ''}

Respond with JSON format only:
{
  "canPreview": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}`;

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openaiKey}`
        },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: 'You are a game code analyzer that determines if a game can be previewed/played directly in a browser. Always respond with valid JSON only, no additional text.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.3,
          max_tokens: 500
        })
      });
      
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`OpenAI API error: ${response.status} - ${errorData}`);
      }
      
      const data = await response.json();
      const aiResponse = data.choices[0]?.message?.content || '';
      
      // Parse AI response
      let aiResult;
      try {
        // Try to extract JSON from response
        const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          aiResult = JSON.parse(jsonMatch[0]);
        } else {
          throw new Error('No JSON found in response');
        }
      } catch (parseError) {
        // Fallback: basic check if it looks like a game
        const hasGameElements = content.includes('<script') || content.includes('game') || content.includes('Game');
        aiResult = {
          canPreview: hasGameElements,
          confidence: 0.5,
          reason: 'Could not analyze properly, basic check performed'
        };
      }
      
      res.json({
        success: true,
        data: {
          canPreview: aiResult.canPreview || false,
          confidence: aiResult.confidence || 0.5,
          reason: aiResult.reason || 'No reason provided'
        }
      });
    } catch (error) {
      console.error('OpenAI API error:', error);
      // Fallback: basic check
      const hasGameElements = content.includes('<script') || content.includes('game') || content.includes('Game');
      res.json({
        success: true,
        data: {
          canPreview: hasGameElements,
          confidence: 0.4,
          reason: 'Analysis failed, basic check performed'
        }
      });
    }
  } catch (error) {
    console.error('Error checking format:', error);
    res.status(500).json({ success: false, message: 'Failed to check format: ' + error.message });
  }
});

// Check folder/repository format
app.post('/api/admin/git/check-folder-format', verifyAdminToken, async (req, res) => {
  try {
    const { provider, owner, repo, branch, path: folderPath } = req.body;
    
    if (!provider || !owner || !repo || !branch) {
      return res.status(400).json({ success: false, message: 'Provider, owner, repo, and branch are required' });
    }
    
    const token = provider === 'github' ? process.env.GITHUB_TOKEN : process.env.GITLAB_TOKEN;
    const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
    
    const openaiKey = process.env.OPENAI_API_KEY;
    if (!openaiKey) {
      return res.status(500).json({ success: false, message: 'OpenAI API key not configured' });
    }
    
    // Get all files in the folder recursively (or at least look for HTML files)
    let htmlFiles = [];
    
    // Function to recursively find HTML files
    async function findHtmlFiles(path = '') {
      try {
        let files = [];
        
        if (provider === 'github') {
          const apiPath = path ? `contents/${path}` : 'contents';
          const apiUrl = `https://api.github.com/repos/${owner}/${repo}/${apiPath}?ref=${branch}`;
          const response = await fetch(apiUrl, { headers: authHeader });
          
          if (!response.ok) return [];
          
          const data = await response.json();
          const items = Array.isArray(data) ? data : [data];
          
          for (const item of items) {
            if (item.type === 'file' && (item.name.endsWith('.html') || item.name.endsWith('.htm'))) {
              files.push(item.path);
            } else if (item.type === 'dir') {
              // Recursively check subdirectories (limit depth to avoid too many API calls)
              if (!path || path.split('/').length < 3) {
                const subFiles = await findHtmlFiles(item.path);
                files.push(...subFiles);
              }
            }
          }
        } else if (provider === 'gitlab') {
          const projectId = encodeURIComponent(`${owner}/${repo}`);
          const apiPath = path ? `tree?path=${encodeURIComponent(path)}&ref=${branch}` : `tree?ref=${branch}`;
          const apiUrl = `https://gitlab.com/api/v4/projects/${projectId}/repository/${apiPath}`;
          const response = await fetch(apiUrl, { headers: authHeader });
          
          if (!response.ok) return [];
          
          const data = await response.json();
          const items = Array.isArray(data) ? data : [];
          
          for (const item of items) {
            if (item.type === 'blob' && (item.name.endsWith('.html') || item.name.endsWith('.htm'))) {
              files.push(item.path);
            } else if (item.type === 'tree') {
              // Recursively check subdirectories (limit depth)
              if (!path || path.split('/').length < 3) {
                const subFiles = await findHtmlFiles(item.path);
                files.push(...subFiles);
              }
            }
          }
        }
        
        return files;
      } catch (error) {
        console.error('Error finding HTML files:', error);
        return [];
      }
    }
    
    // Find HTML files, prioritize index.html
    htmlFiles = await findHtmlFiles(folderPath || '');
    
    // Sort: index.html first
    htmlFiles.sort((a, b) => {
      if (a.toLowerCase().includes('index.html')) return -1;
      if (b.toLowerCase().includes('index.html')) return 1;
      return a.localeCompare(b);
    });
    
    // Check first few HTML files (limit to 5 to avoid too many API calls)
    let bestMatch = null;
    let bestConfidence = 0;
    
    for (const filePath of htmlFiles.slice(0, 5)) {
      try {
        // Get file content
        let content = '';
        if (provider === 'github') {
          const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${filePath}?ref=${branch}`;
          const response = await fetch(apiUrl, { headers: authHeader });
          if (response.ok) {
            const data = await response.json();
            if (data.encoding === 'base64') {
              content = Buffer.from(data.content, 'base64').toString('utf-8');
            }
          }
        } else if (provider === 'gitlab') {
          const projectId = encodeURIComponent(`${owner}/${repo}`);
          const apiUrl = `https://gitlab.com/api/v4/projects/${projectId}/repository/files/${encodeURIComponent(filePath)}/raw?ref=${branch}`;
          const response = await fetch(apiUrl, { headers: authHeader });
          if (response.ok) {
            content = await response.text();
          }
        }
        
        if (!content) continue;
        
        // Check format using AI
        const prompt = `Analyze this HTML/JavaScript code and determine: Can this game be previewed/played directly in a web browser right here?

Consider:
- Does it contain complete game code (HTML, CSS, JavaScript)?
- Can it run standalone without external server requirements?
- Is it a playable game interface?

Here's the code to check:

${content.substring(0, 8000)}${content.length > 8000 ? '... (truncated)' : ''}

Respond with JSON format only:
{
  "canPreview": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}`;
        
        const aiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${openaiKey}`
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages: [
              {
                role: 'system',
                content: 'You are a game code analyzer that determines if a game can be previewed/played directly in a browser. Always respond with valid JSON only, no additional text.'
              },
              {
                role: 'user',
                content: prompt
              }
            ],
            temperature: 0.3,
            max_tokens: 300
          })
        });
        
        if (aiResponse.ok) {
          const data = await aiResponse.json();
          const aiResultText = data.choices[0]?.message?.content || '';
          const jsonMatch = aiResultText.match(/\{[\s\S]*\}/);
          
          if (jsonMatch) {
            const aiResult = JSON.parse(jsonMatch[0]);
            if (aiResult.canPreview && (aiResult.confidence || 0) > bestConfidence) {
              bestMatch = {
                filePath,
                canPreview: true,
                confidence: aiResult.confidence || 0.5,
                reason: aiResult.reason || 'Found playable game'
              };
              bestConfidence = aiResult.confidence || 0;
            }
          }
        }
      } catch (error) {
        console.error(`Error checking file ${filePath}:`, error);
      }
    }
    
    // Return result
    if (bestMatch) {
      res.json({
        success: true,
        data: {
          canPreview: true,
          confidence: bestMatch.confidence,
          reason: bestMatch.reason,
          filePath: bestMatch.filePath
        }
      });
    } else {
      res.json({
        success: true,
        data: {
          canPreview: false,
          confidence: 0.3,
          reason: htmlFiles.length === 0 ? 'No HTML files found in this folder' : 'No playable games found in HTML files',
          filePath: null
        }
      });
    }
  } catch (error) {
    console.error('Error checking folder format:', error);
    res.status(500).json({ success: false, message: 'Failed to check folder format: ' + error.message });
  }
});

// Test endpoint for environment variables (admin only - for testing)
app.get('/api/test-env', verifyAdminToken, (req, res) => {
  const envVars = {
    GITHUB_TOKEN: process.env.GITHUB_TOKEN ? '✓ Set (hidden)' : '✗ Not set',
    GITLAB_TOKEN: process.env.GITLAB_TOKEN ? '✓ Set (hidden)' : '✗ Not set',
    OPENAI_API_KEY: process.env.OPENAI_API_KEY ? '✓ Set (hidden)' : '✗ Not set'
  };
  
  res.json({
    success: true,
    message: 'Environment variables status:',
    variables: envVars,
    note: 'Actual values are hidden for security'
  });
});

// 404 handler - must be last route
app.get('*', (req, res) => {
  res.status(404).sendFile(path.join(__dirname, '404.html'));
});

app.listen(port, () => {
  console.log(`Selenite is running on port ${port}`);
  console.log('\n--- Environment Variables Status ---');
  console.log(`GITHUB_TOKEN: ${process.env.GITHUB_TOKEN ? '✓ Set' : '✗ Not set'}`);
  console.log(`GITLAB_TOKEN: ${process.env.GITLAB_TOKEN ? '✓ Set' : '✗ Not set'}`);
  console.log(`OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? '✓ Set' : '✗ Not set'}`);
  console.log('-----------------------------------\n');
});
