// Simple script to import admin credentials - Just edit the array below and run: node scripts/import-admins-simple.js

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ============================================
// EDIT THIS ARRAY WITH YOUR CREDENTIALS
// ============================================
const CREDENTIALS = [
  { email: 'aaravharjani@icloud.com', password: 'Aarav2014123!!!' },
  { email: 'bestboymg1@gmail.com', password: 'Matusha2013' },
  // Add more like this:
  // { email: 'your-email@example.com', password: 'your-password' },
];
// ============================================

const credentialsPath = path.join(__dirname, '..', 'data', 'admin-credentials.json');

// Read existing
let existing = [];
try {
  if (fs.existsSync(credentialsPath)) {
    existing = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
  }
} catch (error) {
  console.error('Error reading existing credentials:', error);
}

// Hash passwords and add new ones
const existingEmails = new Set(existing.map(c => c.email.toLowerCase()));
let added = 0;
let skipped = 0;

CREDENTIALS.forEach(cred => {
  const email = cred.email.toLowerCase();
  
  if (existingEmails.has(email)) {
    console.log(`⚠ Skipped ${cred.email} (already exists)`);
    skipped++;
    return;
  }

  existing.push({
    email: cred.email,
    password: crypto.createHash('sha256').update(cred.password).digest('hex'),
    createdAt: new Date().toISOString()
  });
  
  existingEmails.add(email);
  console.log(`✓ Added ${cred.email}`);
  added++;
});

// Write back
fs.writeFileSync(credentialsPath, JSON.stringify(existing, null, 2), 'utf8');

console.log(`\n✅ Done! ${added} added, ${skipped} skipped, ${existing.length} total credentials`);

