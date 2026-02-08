# Add Admin Accounts

## Quick Method (Easiest)

1. Open `scripts/import-admins-simple.js`
2. Edit the `CREDENTIALS` array:
   ```javascript
   const CREDENTIALS = [
     { email: 'admin@example.com', password: 'admin123' },
     { email: 'admin2@example.com', password: 'password456' },
     // Add more accounts here
   ];
   ```
3. Run: `node scripts/import-admins-simple.js`

## Alternative: Programmatic Import

You can also import from any Node.js file:

```javascript
const { importAdminCredentials } = require('./index.js');

importAdminCredentials([
  { email: 'admin@example.com', password: 'admin123' },
  { email: 'admin2@example.com', password: 'password456' },
]);
```

## File Location

- **Script to edit**: `scripts/import-admins-simple.js`
- **Credentials stored in**: `data/admin-credentials.json`

Passwords are automatically hashed and duplicate emails are skipped.
