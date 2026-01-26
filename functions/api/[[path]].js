// Cloudflare Workers function to handle all API routes
// This replaces the Express.js API endpoints

// Helper function to get IP address from request
function getClientIp(request) {
  const cfConnectingIp = request.headers.get('cf-connecting-ip');
  const xForwardedFor = request.headers.get('x-forwarded-for');
  const xRealIp = request.headers.get('x-real-ip');
  
  if (cfConnectingIp) return cfConnectingIp;
  if (xForwardedFor) return xForwardedFor.split(',')[0].trim();
  if (xRealIp) return xRealIp;
  return '127.0.0.1';
}

// Helper function to hash password using Web Crypto API
async function hashPassword(password) {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Helper function to generate random token
function generateToken() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
}

// KV helper functions
async function readKV(kv, key, defaultValue = {}) {
  try {
    const value = await kv.get(key);
    if (!value) return defaultValue;
    return JSON.parse(value);
  } catch (error) {
    console.error(`Error reading KV key ${key}:`, error);
    return defaultValue;
  }
}

async function writeKV(kv, key, data) {
  try {
    await kv.put(key, JSON.stringify(data));
    return true;
  } catch (error) {
    console.error(`Error writing KV key ${key}:`, error);
    return false;
  }
}

// Verify admin token
async function verifyAdminToken(request, env) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return { valid: false };
  }

  const token = authHeader.substring(7);
  const tokenData = await readKV(env.TOKENS_KV, `token:${token}`, null);
  
  if (!tokenData || !tokenData.authenticated) {
    return { valid: false };
  }

  // Check if token is expired
  if (tokenData.expiresAt && new Date(tokenData.expiresAt) < new Date()) {
    return { valid: false };
  }

  return { valid: true };
}

// JSON response helper
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Main request handler
export async function onRequest(context) {
  const { request, env, params } = context;
  const url = new URL(request.url);
  const path = params.path || [];
  const pathname = url.pathname;
  const method = request.method;

  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  };

  // Handle OPTIONS requests
  if (method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Route: POST /api/submit-suggestion
    if (pathname === '/api/submit-suggestion' && method === 'POST') {
      const body = await request.json();
      const { type, title, description, email, steps } = body;
      
      const clientIp = getClientIp(request);
      
      if (!type || !title) {
        return jsonResponse({ success: false, message: 'Type and title are required' }, 400);
      }

      const suggestions = await readKV(env.SUGGESTIONS_KV, 'suggestions', {
        gameSuggestions: [],
        featureSuggestions: [],
        bugReports: []
      });

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
        return jsonResponse({ success: false, message: 'Invalid type. Must be game, feature, or bug' }, 400);
      }

      if (await writeKV(env.SUGGESTIONS_KV, 'suggestions', suggestions)) {
        return jsonResponse({ success: true, message: 'Thank you! Your message has been sent successfully.' });
      } else {
        return jsonResponse({ success: false, message: 'Failed to save suggestion' }, 500);
      }
    }

    // Route: POST /api/admin/login
    if (pathname === '/api/admin/login' && method === 'POST') {
      const body = await request.json();
      const { password } = body;

      if (!password) {
        return jsonResponse({ success: false, message: 'Password required' }, 400);
      }

      // Get stored password hash, or initialize with default password
      let storedPasswordHash = await readKV(env.ADMIN_CREDENTIALS_KV, 'admin_password', null);
      
      // If no password is set, initialize with default password hash
      if (!storedPasswordHash) {
        const defaultPassword = 'nova_admin_aarav_matthew';
        storedPasswordHash = await hashPassword(defaultPassword);
        await writeKV(env.ADMIN_CREDENTIALS_KV, 'admin_password', storedPasswordHash);
      }

      const hashedPassword = await hashPassword(password);

      if (hashedPassword !== storedPasswordHash) {
        return jsonResponse({ success: false, message: 'Invalid password' }, 401);
      }

      const token = generateToken();
      const tokenData = {
        authenticated: true,
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
      };

      await writeKV(env.TOKENS_KV, `token:${token}`, tokenData);

      return jsonResponse({ success: true, token });
    }

    // Route: GET /api/admin/verify
    if (pathname === '/api/admin/verify' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }
      return jsonResponse({ success: true });
    }

    // Route: POST /api/admin/emergency-reset
    // ⚠️ TEMPORARY: Remove this endpoint after resetting your password!
    // This resets the admin password to the default: 'nova_admin_aarav_matthew'
    if (pathname === '/api/admin/emergency-reset' && method === 'POST') {
      const defaultPassword = 'adminnova';
      const hashedDefaultPassword = await hashPassword(defaultPassword);
      
      if (await writeKV(env.ADMIN_CREDENTIALS_KV, 'admin_password', hashedDefaultPassword)) {
        return jsonResponse({ 
          success: true, 
          message: 'Password reset to default. Default password: adminnova. Please change it immediately after logging in and REMOVE THIS ENDPOINT!' 
        });
      } else {
        return jsonResponse({ success: false, message: 'Failed to reset password' }, 500);
      }
    }

    // Route: POST /api/admin/change-password
    if (pathname === '/api/admin/change-password' && method === 'POST') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const body = await request.json();
      const { newPassword } = body;

      if (!newPassword) {
        return jsonResponse({ success: false, message: 'New password is required' }, 400);
      }

      if (newPassword.length < 8) {
        return jsonResponse({ success: false, message: 'New password must be at least 8 characters long' }, 400);
      }

      // Set new password (no need to verify old password since user is already authenticated)
      const hashedNewPassword = await hashPassword(newPassword);
      
      if (await writeKV(env.ADMIN_CREDENTIALS_KV, 'admin_password', hashedNewPassword)) {
        return jsonResponse({ success: true, message: 'Password changed successfully' });
      } else {
        return jsonResponse({ success: false, message: 'Failed to change password' }, 500);
      }
    }

    // Route: GET /api/admin/suggestions
    if (pathname === '/api/admin/suggestions' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const suggestions = await readKV(env.SUGGESTIONS_KV, 'suggestions', {
        gameSuggestions: [],
        featureSuggestions: [],
        bugReports: []
      });
      return jsonResponse({ success: true, data: suggestions });
    }

    // Route: POST /api/admin/delete-suggestion
    if (pathname === '/api/admin/delete-suggestion' && method === 'POST') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const body = await request.json();
      const { type, index } = body;

      if (!type || typeof index === 'undefined' || index === null) {
        return jsonResponse({ success: false, message: 'Type and index are required' }, 400);
      }

      const indexNum = parseInt(index, 10);
      if (isNaN(indexNum) || indexNum < 0) {
        return jsonResponse({ success: false, message: 'Index must be a valid non-negative number' }, 400);
      }

      const suggestions = await readKV(env.SUGGESTIONS_KV, 'suggestions', {
        gameSuggestions: [],
        featureSuggestions: [],
        bugReports: []
      });

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
        return jsonResponse({ success: false, message: 'Invalid type. Must be game, feature, or bug' }, 400);
      }

      if (indexNum >= targetArray.length) {
        return jsonResponse({ success: false, message: `Invalid index: ${indexNum}. Array length is ${targetArray.length}` }, 400);
      }

      targetArray.splice(indexNum, 1);

      if (await writeKV(env.SUGGESTIONS_KV, 'suggestions', suggestions)) {
        return jsonResponse({ success: true, message: 'Suggestion deleted successfully' });
      } else {
        return jsonResponse({ success: false, message: 'Failed to save changes' }, 500);
      }
    }

    // Route: GET /api/admin/analytics
    if (pathname === '/api/admin/analytics' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const analytics = await readKV(env.ANALYTICS_KV, 'analytics', {
        totalUsers: 0,
        todayVisits: 0,
        pageViews: 0,
        lastUpdated: null
      });

      // Calculate live users (simplified - in production, use a more sophisticated method)
      const liveUsers = 0; // You can implement this with Durable Objects or another method

      return jsonResponse({
        success: true,
        liveUsers: liveUsers,
        totalUsers: analytics.totalUsers || 0,
        todayVisits: analytics.todayVisits || 0,
        pageViews: analytics.pageViews || 0
      });
    }

    // Route: GET /api/admin/ga-id
    if (pathname === '/api/admin/ga-id' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const analytics = await readKV(env.ANALYTICS_KV, 'analytics', {});
      return jsonResponse({ success: true, gaId: analytics.gaMeasurementId || '' });
    }

    // Route: POST /api/admin/save-ga-id
    if (pathname === '/api/admin/save-ga-id' && method === 'POST') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const body = await request.json();
      const { gaId } = body;

      const analytics = await readKV(env.ANALYTICS_KV, 'analytics', {});
      analytics.gaMeasurementId = gaId || '';
      analytics.lastUpdated = new Date().toISOString();

      if (await writeKV(env.ANALYTICS_KV, 'analytics', analytics)) {
        return jsonResponse({ success: true });
      } else {
        return jsonResponse({ success: false, message: 'Failed to save GA ID' }, 500);
      }
    }

    // Route: POST /api/track-visit
    if (pathname === '/api/track-visit' && method === 'POST') {
      const analytics = await readKV(env.ANALYTICS_KV, 'analytics', {
        totalUsers: 0,
        todayVisits: 0,
        pageViews: 0,
        lastUpdated: null
      });

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

      await writeKV(env.ANALYTICS_KV, 'analytics', analytics);
      return jsonResponse({ success: true });
    }

    // Route: GET /api/terminal-text (public endpoint) — same KV as admin (ADMIN_CREDENTIALS_KV)
    if (pathname === '/api/terminal-text' && method === 'GET') {
      const terminalText = await readKV(env.ADMIN_CREDENTIALS_KV, 'terminal_text', {
        welcomeLines: ['Welcome to Nova Hub', 'Your ultimate gaming destination'],
        statusText: 'If you see this, it loaded.'
      });
      return jsonResponse({ success: true, data: terminalText });
    }

    // Route: GET /api/admin/terminal-text
    if (pathname === '/api/admin/terminal-text' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const terminalText = await readKV(env.ADMIN_CREDENTIALS_KV, 'terminal_text', {
        welcomeLines: ['Welcome to Nova Hub', 'Your ultimate gaming destination'],
        statusText: 'If you see this, it loaded.'
      });
      return jsonResponse({ success: true, data: terminalText });
    }

    // Route: POST /api/admin/save-terminal-text
    if (pathname === '/api/admin/save-terminal-text' && method === 'POST') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }

      const body = await request.json();
      const { welcomeLines, statusText } = body;

      if (!Array.isArray(welcomeLines) || !statusText) {
        return jsonResponse({ success: false, message: 'welcomeLines (array) and statusText (string) are required' }, 400);
      }

      const terminalText = {
        welcomeLines: welcomeLines,
        statusText: statusText,
        lastUpdated: new Date().toISOString()
      };

      if (await writeKV(env.ADMIN_CREDENTIALS_KV, 'terminal_text', terminalText)) {
        return jsonResponse({ success: true, message: 'Terminal text saved successfully' });
      } else {
        return jsonResponse({ success: false, message: 'Failed to save terminal text' }, 500);
      }
    }

    // Route: GET /api/banner (public) — same KV as admin (ADMIN_CREDENTIALS_KV)
    if (pathname === '/api/banner' && method === 'GET') {
      const banner = await readKV(env.ADMIN_CREDENTIALS_KV, 'banner', {
        enabled: false,
        text: ''
      });
      return jsonResponse({ success: true, data: banner });
    }

    // Route: GET /api/admin/banner
    if (pathname === '/api/admin/banner' && method === 'GET') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }
      const banner = await readKV(env.ADMIN_CREDENTIALS_KV, 'banner', {
        enabled: false,
        text: ''
      });
      return jsonResponse({ success: true, data: banner });
    }

    // Route: POST /api/admin/save-banner
    if (pathname === '/api/admin/save-banner' && method === 'POST') {
      const auth = await verifyAdminToken(request, env);
      if (!auth.valid) {
        return jsonResponse({ success: false, message: 'Invalid token' }, 401);
      }
      const body = await request.json();
      const { enabled, text } = body;
      const banner = {
        enabled: !!enabled,
        text: typeof text === 'string' ? text : '',
        lastUpdated: new Date().toISOString()
      };
      if (await writeKV(env.ADMIN_CREDENTIALS_KV, 'banner', banner)) {
        return jsonResponse({ success: true, message: 'Banner saved successfully' });
      } else {
        return jsonResponse({ success: false, message: 'Failed to save banner' }, 500);
      }
    }

    // Route not found
    return jsonResponse({ success: false, message: 'Not found' }, 404);

  } catch (error) {
    console.error('API Error:', error);
    return jsonResponse({ success: false, message: 'Internal server error: ' + error.message }, 500);
  }
}

