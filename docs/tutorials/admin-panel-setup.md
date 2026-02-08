# Admin Panel Setup

## What Has Been Created

1. **Admin Page** (`/admin.html`) - Login page with analytics dashboard
2. **Admin Authentication** - Secure login system with token-based authentication
3. **Credentials Management** - Easy import system for admin emails and passwords
4. **Analytics Dashboard** - Display for Google Analytics and site statistics

## How to Access

1. Navigate to `http://localhost:3000/admin` (or your domain/admin)
2. Use the default credentials:
   - Email: `admin@example.com`
   - Password: `admin123`

## Importing Admin Credentials

### Method 1: Through Code (Recommended)

**Option A: Simple Script**
1. Edit `scripts/import-admins-simple.js`
2. Add your credentials to the `CREDENTIALS` array:
   ```javascript
   const CREDENTIALS = [
     { email: 'admin@example.com', password: 'admin123' },
     { email: 'admin2@example.com', password: 'password456' },
   ];
   ```
3. Run: `node scripts/import-admins-simple.js`

**Option B: Programmatic Import**
```javascript
const { importAdminCredentials } = require('./index.js');

importAdminCredentials([
  { email: 'admin@example.com', password: 'admin123' },
  { email: 'admin2@example.com', password: 'password456' },
]);
```

**Option C: Advanced Script**
1. Edit `scripts/import-admins.js`
2. Modify the `credentialsToImport` array
3. Run: `node scripts/import-admins.js`

### Method 2: Through Website

1. Login to the admin panel
2. In the "Import Admin Credentials" section, paste credentials in this format:
   ```
   email1@example.com:password1
   email2@example.com:password2
   email3@example.com:password3
   ```
3. Click "Import Credentials"
4. Each credential will be hashed and stored securely

## What You Need to Link Up

### 1. Google Analytics Live Users

**Current Status:** Placeholder (shows 0)

**To Enable:**
- You need to integrate with the Google Analytics Reporting API
- Required:
  - Google Analytics 4 (GA4) Property ID
  - Service Account JSON key file
  - Enable the Analytics Reporting API in Google Cloud Console

**Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Analytics Reporting API"
4. Create a Service Account and download JSON key
5. Install Google Analytics library: `npm install googleapis`
6. Update `/api/admin/analytics` endpoint in `index.js` to fetch real-time data

**Alternative:** Use Google Analytics Measurement Protocol or embed GA4 directly in your pages and use the GA4 Data API.

### 2. Total Users of All Time

**Current Status:** Tracks visits via `/api/track-visit` endpoint

**To Enable:**
- Add this script to your main pages (index.html, etc.):
  ```javascript
  fetch('/api/track-visit', { method: 'POST' });
  ```
- Or integrate with your existing analytics system
- The data is stored in `data/analytics.json`

**To Link External Data:**
- If you have user data in a database, update the `/api/admin/analytics` endpoint to query your database
- Replace the file-based storage with database queries

### 3. Today's Visits

**Current Status:** Tracks via `/api/track-visit` endpoint

**To Enable:**
- Same as above - add the tracking script to your pages
- Or integrate with Google Analytics API to get daily visit counts

### 4. Total Page Views

**Current Status:** Tracks via `/api/track-visit` endpoint

**To Enable:**
- Same tracking script as above
- Or pull from Google Analytics API

## Database Integration (Optional but Recommended)

Currently, the system uses JSON files for storage. For production, consider:

1. **Replace file storage with database:**
   - MongoDB, PostgreSQL, or MySQL
   - Update `readJsonFile` and `writeJsonFile` functions to use database queries

2. **User tracking:**
   - Store unique user sessions
   - Track user behavior
   - Store analytics data in database instead of JSON

## Google Analytics Integration Code Example

To add real Google Analytics integration, update the `/api/admin/analytics` endpoint in `index.js`:

```javascript
const { google } = require('googleapis');

app.get('/api/admin/analytics', verifyAdminToken, async (req, res) => {
  const analyticsPath = path.join(__dirname, 'data', 'analytics.json');
  const analytics = readJsonFile(analyticsPath);
  
  // Google Analytics API integration
  const auth = new google.auth.GoogleAuth({
    keyFile: 'path/to/service-account-key.json',
    scopes: ['https://www.googleapis.com/auth/analytics.readonly']
  });
  
  const analyticsReporting = google.analyticsdata('v1beta');
  
  try {
    // Get real-time active users
    const response = await analyticsReporting.properties.runRealtimeReport({
      auth: auth,
      property: `properties/${analytics.gaMeasurementId}`,
      requestBody: {
        metrics: [{ name: 'activeUsers' }]
      }
    });
    
    const liveUsers = response.data.rows?.[0]?.metricValues?.[0]?.value || 0;
    
    res.json({
      success: true,
      liveUsers: parseInt(liveUsers),
      totalUsers: analytics.totalUsers || 0,
      todayVisits: analytics.todayVisits || 0,
      pageViews: analytics.pageViews || 0
    });
  } catch (error) {
    console.error('GA API Error:', error);
    res.json({
      success: true,
      liveUsers: 0,
      totalUsers: analytics.totalUsers || 0,
      todayVisits: analytics.todayVisits || 0,
      pageViews: analytics.pageViews || 0
    });
  }
});
```

## Security Notes

1. **Change default password** - The default `admin@example.com:admin123` should be changed immediately
2. **Use HTTPS** - Always use HTTPS in production
3. **Token expiration** - Currently tokens don't expire (stored in memory). For production:
   - Add token expiration
   - Use Redis or database for token storage
   - Implement refresh tokens

## File Structure

```
data/
  ├── admin-credentials.json  # Admin login credentials (hashed passwords)
  └── analytics.json           # Analytics data storage

js/
  └── admin.js                # Admin panel frontend logic

admin.html                    # Admin panel page
```

## API Endpoints

- `POST /api/admin/login` - Admin login
- `GET /api/admin/verify` - Verify admin token
- `POST /api/admin/import-credentials` - Import admin credentials
- `GET /api/admin/count` - Get admin count
- `GET /api/admin/analytics` - Get analytics data
- `GET /api/admin/ga-id` - Get Google Analytics ID
- `POST /api/admin/save-ga-id` - Save Google Analytics ID
- `POST /api/track-visit` - Track page visit (call from your main site)

## Next Steps

1. **Immediate:**
   - Change default admin password
   - Add tracking script to your main pages
   - Set up Google Analytics Measurement ID

2. **Short-term:**
   - Integrate Google Analytics API for live users
   - Add more analytics metrics
   - Implement user session tracking

3. **Long-term:**
   - Migrate to database storage
   - Add more admin features (user management, content moderation, etc.)
   - Implement proper token expiration and refresh
