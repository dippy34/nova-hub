const fs = require('fs');
const path = require('path');

// Read zones.json to map game names to IDs
const zonesPath = path.join(__dirname, 'gn-math-assets', 'zones.json');
const zonesData = JSON.parse(fs.readFileSync(zonesPath, 'utf8'));

// Read games.json
const gamesPath = path.join(__dirname, 'data', 'games.json');
const games = JSON.parse(fs.readFileSync(gamesPath, 'utf8'));

// Create map of directory to game ID
const directoryToId = new Map();
zonesData.forEach(zone => {
    if (zone.id >= 0 && zone.name) {
        // Find matching game in games.json by name
        const matchingGame = games.find(g => {
            const zoneName = zone.name.toLowerCase().trim().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ');
            const gameName = g.name.toLowerCase().trim().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ');
            return zoneName === gameName;
        });
        if (matchingGame) {
            directoryToId.set(matchingGame.directory.toLowerCase(), zone.id);
        }
    }
});

// HTML files directory
const htmlDir = path.join(__dirname, 'gn-math-html');
const htmlFiles = new Map();

// Load all HTML files
if (fs.existsSync(htmlDir)) {
    fs.readdirSync(htmlDir).forEach(file => {
        if (file.endsWith('.html')) {
            const match = file.match(/^(\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                const filePath = path.join(htmlDir, file);
                htmlFiles.set(id, filePath);
            }
        }
    });
}

console.log(`Loaded ${htmlFiles.size} HTML files`);
console.log(`Mapped ${directoryToId.size} game directories to IDs`);

// Create semag directory structure
const semagDir = path.join(__dirname, 'semag');
if (!fs.existsSync(semagDir)) {
    fs.mkdirSync(semagDir, { recursive: true });
}

let copiedCount = 0;
let missingCount = 0;
const missingGames = [];

// Copy HTML files to match directory structure
directoryToId.forEach((gameId, directory) => {
    const htmlFile = htmlFiles.get(gameId);
    if (htmlFile) {
        const gameDir = path.join(semagDir, directory);
        if (!fs.existsSync(gameDir)) {
            fs.mkdirSync(gameDir, { recursive: true });
        }
        const destFile = path.join(gameDir, 'index.html');
        try {
            fs.copyFileSync(htmlFile, destFile);
            copiedCount++;
            if (copiedCount % 50 === 0) {
                console.log(`  Copied ${copiedCount} games...`);
            }
        } catch (error) {
            console.error(`  Error copying ${directory}: ${error.message}`);
        }
    } else {
        missingCount++;
        missingGames.push({ directory, gameId });
    }
});

console.log(`\n✅ Copied ${copiedCount} HTML files to semag/ directory`);
console.log(`❌ ${missingCount} games don't have HTML files`);

if (missingGames.length > 0 && missingGames.length <= 20) {
    console.log('\nMissing HTML files for:');
    missingGames.slice(0, 20).forEach(({ directory, gameId }) => {
        console.log(`  - ${directory} (ID: ${gameId})`);
    });
}

console.log('\n💡 HTML files are now in semag/{directory}/index.html format');
console.log('   Games should now work when accessed via loader.html');

