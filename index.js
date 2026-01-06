const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

// Hardcoded primary admin account
const PRIMARY_ADMIN = {
  email: 'aaravharjani@icloud.com',
  password: 'Aarav2014123!!!' // Password in code as requested
};

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

  if (!adminData) {
    return res.status(401).json({ success: false, message: 'Invalid token' });
  }

  req.adminEmail = adminData.email;
  next();
}

// Admin API Routes
app.post('/api/admin/login', (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ success: false, message: 'Email and password required' });
    }

    // Check hardcoded primary admin first
    if (email.toLowerCase() === PRIMARY_ADMIN.email.toLowerCase() && password === PRIMARY_ADMIN.password) {
      const token = generateToken();
      activeTokens[token] = { email: PRIMARY_ADMIN.email };
      return res.json({ success: true, token, email: PRIMARY_ADMIN.email });
    }

    // Check other admin accounts from file
    const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
    const credentials = readJsonFile(credentialsPath);

    if (credentials.length === 0) {
      return res.status(401).json({ success: false, message: 'Invalid credentials' });
    }

    const hashedPassword = hashPassword(password);
    const admin = credentials.find(cred => cred.email.toLowerCase() === email.toLowerCase() && cred.password === hashedPassword);

    if (!admin) {
      return res.status(401).json({ success: false, message: 'Invalid credentials' });
    }

    const token = generateToken();
    activeTokens[token] = { email: admin.email };
    res.json({ success: true, token, email: admin.email });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ success: false, message: 'Server error during login' });
  }
});

app.get('/api/admin/verify', verifyAdminToken, (req, res) => {
  res.json({ success: true, email: req.adminEmail });
});

app.post('/api/admin/import-credentials', verifyAdminToken, (req, res) => {
  const { credentials } = req.body;

  if (!Array.isArray(credentials) || credentials.length === 0) {
    return res.status(400).json({ success: false, message: 'Invalid credentials format' });
  }

  const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
  const existingCredentials = readJsonFile(credentialsPath);

  let count = 0;
  credentials.forEach(cred => {
    if (cred.email && cred.password) {
      // Check if email already exists
      const exists = existingCredentials.find(c => c.email === cred.email);
      if (!exists) {
        existingCredentials.push({
          email: cred.email,
          password: hashPassword(cred.password),
          createdAt: new Date().toISOString()
        });
        count++;
      }
    }
  });

  if (writeJsonFile(credentialsPath, existingCredentials)) {
    res.json({ success: true, count });
  } else {
    res.status(500).json({ success: false, message: 'Failed to save credentials' });
  }
});

app.get('/api/admin/count', verifyAdminToken, (req, res) => {
  const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
  const credentials = readJsonFile(credentialsPath);
  // Count includes the primary admin + file-based admins
  res.json({ success: true, count: 1 + credentials.length });
});

// Create new admin account
app.post('/api/admin/create-account', verifyAdminToken, async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ success: false, message: 'Email and password are required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ success: false, message: 'Invalid email format' });
    }

    // Don't allow creating account with primary admin email
    if (email.toLowerCase() === PRIMARY_ADMIN.email.toLowerCase()) {
      return res.status(400).json({ success: false, message: 'This email is reserved for the primary admin' });
    }

    const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
    let credentials = readJsonFile(credentialsPath);
    
    // Ensure it's an array
    if (!Array.isArray(credentials)) {
      credentials = [];
    }

    // Check if email already exists
    const existingEmails = new Set(credentials.map(c => c.email.toLowerCase()));
    if (existingEmails.has(email.toLowerCase())) {
      return res.status(400).json({ success: false, message: 'An admin account with this email already exists' });
    }

    // Add new admin account
    credentials.push({
      email: email,
      password: hashPassword(password),
      createdAt: new Date().toISOString()
    });

    // Write to file
    if (!writeJsonFile(credentialsPath, credentials)) {
      return res.status(500).json({ success: false, message: 'Failed to save admin account' });
    }

    res.json({ success: true, message: 'Admin account created successfully' });
  } catch (error) {
    console.error('Create admin account error:', error);
    res.status(500).json({ success: false, message: 'Server error: ' + error.message });
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

// 404 handler - must be last route
app.get('*', (req, res) => {
  res.status(404).sendFile(path.join(__dirname, '404.html'));
});

app.listen(port, () => {
  console.log(`Selenite is running on port ${port}`);
});
