const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { google } = require('googleapis');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.static(__dirname));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/projects', (req, res) => {
  res.sendFile(path.join(__dirname, 'projects.html'));
});

app.get('/bookmarklets', (req, res) => {
  res.sendFile(path.join(__dirname, 'bookmarklets.html'));
});

app.get('/settings', (req, res) => {
  res.sendFile(path.join(__dirname, 'settings.html'));
});

app.get('/support', (req, res) => {
  res.sendFile(path.join(__dirname, 'support.html'));
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

app.get('/contact', (req, res) => {
  res.sendFile(path.join(__dirname, 'contact.html'));
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
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
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
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ success: false, message: 'Email and password required' });
  }

  const credentialsPath = path.join(__dirname, 'data', 'admin-credentials.json');
  const credentials = readJsonFile(credentialsPath);

  const hashedPassword = hashPassword(password);
  const admin = credentials.find(cred => cred.email === email && cred.password === hashedPassword);

  if (!admin) {
    // Check if password is stored as plain text (for initial setup)
    const adminPlain = credentials.find(cred => cred.email === email && cred.password === password);
    if (adminPlain) {
      // Update to hashed password
      adminPlain.password = hashedPassword;
      writeJsonFile(credentialsPath, credentials);
      const token = generateToken();
      activeTokens[token] = { email: adminPlain.email };
      return res.json({ success: true, token, email: adminPlain.email });
    }
    return res.status(401).json({ success: false, message: 'Invalid credentials' });
  }

  const token = generateToken();
  activeTokens[token] = { email: admin.email };
  res.json({ success: true, token, email: admin.email });
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
  res.json({ success: true, count: credentials.length });
});

app.get('/api/admin/analytics', verifyAdminToken, async (req, res) => {
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);

  let liveUsers = 0;
  let todayVisits = 0;
  let totalPageViews = 0;

  // Fetch from Google Analytics if configured
  if (analytics.gaMeasurementId) {
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

app.listen(port, () => {
  console.log(`Selenite is running on port ${port}`);
});
