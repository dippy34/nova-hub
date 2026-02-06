#!/usr/bin/env node
/**
 * Upload game folders to R2 bucket (nova-hub) under semag/ prefix.
 *
 * Usage:
 *   node scripts/upload-game-to-r2.js semag              # Upload ALL games from semag/
 *   node scripts/upload-game-to-r2.js semag/happywheels  # Upload single game
 *
 * R2 keys: semag/{gameName}/index.html, semag/{gameName}/image.png, etc.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const BUCKET = 'nova-hub';
const R2_PREFIX = 'semag';

function getAllFiles(dir, baseDir = dir) {
  const files = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const relPath = path.relative(baseDir, fullPath);
    if (entry.isDirectory()) {
      files.push(...getAllFiles(fullPath, baseDir));
    } else {
      files.push(relPath);
    }
  }
  return files;
}

function uploadFolder(absPath, r2KeyPrefix) {
  const files = getAllFiles(absPath);
  let uploaded = 0;
  let failed = 0;
  for (const file of files) {
    const localPath = path.join(absPath, file);
    const r2Key = `${r2KeyPrefix}/${file.replace(/\\/g, '/')}`;
    try {
      execSync(`npx wrangler r2 object put ${BUCKET}/${r2Key} --file="${localPath}"`, {
        stdio: 'pipe'
      });
      uploaded++;
      process.stdout.write('.');
    } catch (err) {
      failed++;
      console.error(`\n  ✗ ${file}: ${err.message}`);
    }
  }
  return { uploaded, failed };
}

function main() {
  const gamePath = process.argv[2];
  if (!gamePath) {
    console.error('Usage: node scripts/upload-game-to-r2.js <semag|semag/gamename>');
    console.error('  semag              - upload entire semag directory (all games)');
    console.error('  semag/happywheels  - upload single game');
    process.exit(1);
  }

  const absPath = path.resolve(process.cwd(), gamePath);
  if (!fs.existsSync(absPath)) {
    console.error(`Error: Path not found: ${absPath}`);
    process.exit(1);
  }

  const stat = fs.statSync(absPath);
  if (!stat.isDirectory()) {
    console.error('Error: Path must be a directory');
    process.exit(1);
  }

  const basename = path.basename(absPath);
  const isFullSemag = basename === 'semag' && gamePath.replace(/\\/g, '/').endsWith('semag');

  let totalUploaded = 0;
  let totalFailed = 0;

  if (isFullSemag) {
    // Upload entire semag/ - each subfolder becomes semag/{gameName}/...
    const gameDirs = fs.readdirSync(absPath, { withFileTypes: true })
      .filter(e => e.isDirectory())
      .map(e => e.name);
    console.log(`Uploading ${gameDirs.length} games from semag/ to R2...`);
    for (const gameName of gameDirs) {
      const gamePath = path.join(absPath, gameName);
      process.stdout.write(`${gameName} `);
      const { uploaded, failed } = uploadFolder(gamePath, `${R2_PREFIX}/${gameName}`);
      totalUploaded += uploaded;
      totalFailed += failed;
      console.log(` (${uploaded} files)`);
    }
  } else {
    // Single game folder
    const folderName = basename;
    console.log(`Uploading ${folderName} to R2 (${BUCKET}/semag/${folderName}/)...`);
    const { uploaded, failed } = uploadFolder(absPath, `${R2_PREFIX}/${folderName}`);
    totalUploaded = uploaded;
    totalFailed = failed;
    console.log(`\nDone. Uploaded: ${uploaded}, Failed: ${failed}`);
  }

  console.log(`\nTotal: ${totalUploaded} uploaded, ${totalFailed} failed`);
}

main();
