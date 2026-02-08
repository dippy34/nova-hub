const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

// Read games.json
const gamesPath = path.join(ROOT, 'data', 'games.json');
const games = JSON.parse(fs.readFileSync(gamesPath, 'utf8'));

// Read zones.json to map game names to IDs
const zonesPath = path.join(ROOT, 'gn-math-assets', 'zones.json');
const zonesData = JSON.parse(fs.readFileSync(zonesPath, 'utf8'));

// Create map of game name to ID
const gameNameToId = new Map();
zonesData.forEach(zone => {
    if (zone.id >= 0 && zone.name) {
        const normalizedName = zone.name.toLowerCase().trim()
            .replace(/[^\w\s]/g, '')
            .replace(/\s+/g, ' ');
        gameNameToId.set(normalizedName, zone.id);
    }
});

// Check img directory
const imgDir = path.join(ROOT, 'img');
const imgFiles = new Set();
if (fs.existsSync(imgDir)) {
    fs.readdirSync(imgDir, { recursive: true }).forEach(file => {
        imgFiles.add(file);
    });
}

// Check HTML files in gn-math-html
const htmlDir = path.join(ROOT, 'gn-math-html');
const htmlFiles = new Set();
if (fs.existsSync(htmlDir)) {
    fs.readdirSync(htmlDir).forEach(file => {
        if (file.endsWith('.html')) {
            // Extract ID from filename (e.g., "0.html" -> 0, "8-aad.html" -> 8)
            const match = file.match(/^(\d+)/);
            if (match) {
                htmlFiles.add(parseInt(match[1]));
            }
        }
    });
}

// Check non-semag directory (local games)
const nonSemagDir = path.join(ROOT, 'non-semag');
const localGameDirs = new Set();
if (fs.existsSync(nonSemagDir)) {
    fs.readdirSync(nonSemagDir, { withFileTypes: true }).forEach(dirent => {
        if (dirent.isDirectory()) {
            localGameDirs.add(dirent.name.toLowerCase());
        }
    });
}

// Check gn-math-assets (cloned repo with game files)
const gnMathAssetsDir = path.join(__dirname, 'gn-math-assets');
const gnMathGameDirs = new Set();
if (fs.existsSync(gnMathAssetsDir)) {
    fs.readdirSync(gnMathAssetsDir, { withFileTypes: true }).forEach(dirent => {
        if (dirent.isDirectory() && dirent.name.match(/^\d+$/)) {
            const indexPath = path.join(gnMathAssetsDir, dirent.name, 'index.html');
            if (fs.existsSync(indexPath)) {
                gnMathGameDirs.add(parseInt(dirent.name));
            }
        }
    });
}

// Function to normalize game name for comparison
function normalizeName(name) {
    return name.toLowerCase().trim()
        .replace(/[^\w\s]/g, '')
        .replace(/\s+/g, ' ');
}

// Analyze games
const fullyDone = []; // Has HTML + Image
const hasHTML = []; // Has HTML but no image
const hasImage = []; // Has image but no HTML
const hasLocalFiles = []; // Has local files
const missingEverything = []; // Missing HTML, image, and local files

games.forEach(game => {
    const normalizedName = normalizeName(game.name);
    const gameId = gameNameToId.get(normalizedName);
    
    const hasImg = imgFiles.has(game.image) || 
                   imgFiles.has(path.join('backgrounds', game.image)) ||
                   imgFiles.has(path.join('badges', game.image)) ||
                   imgFiles.has(path.join('pfps', game.image));
    
    // Check if image exists in gn-math-assets numbered directories
    let hasGnMathImage = false;
    if (game.image && game.image.match(/^\d+\.png$/)) {
        const imageId = game.image.replace('.png', '');
        const coverPath = path.join(gnMathAssetsDir, imageId, 'cover.png');
        if (fs.existsSync(coverPath)) {
            hasGnMathImage = true;
        }
    }
    
    const imageExists = hasImg || hasGnMathImage;
    const hasHTMLFile = gameId !== undefined && htmlFiles.has(gameId);
    const hasLocal = localGameDirs.has(game.directory.toLowerCase()) ||
                     (gameId !== undefined && gnMathGameDirs.has(gameId));
    
    if (hasHTMLFile && imageExists) {
        fullyDone.push({ ...game, id: gameId });
    } else if (hasHTMLFile) {
        hasHTML.push({ ...game, id: gameId });
    } else if (imageExists) {
        hasImage.push({ ...game, id: gameId });
    } else if (hasLocal) {
        hasLocalFiles.push({ ...game, id: gameId });
    } else {
        missingEverything.push({ ...game, id: gameId });
    }
});

console.log('='.repeat(70));
console.log('GAME STATUS SUMMARY (Updated with HTML files)');
console.log('='.repeat(70));
console.log(`\nTotal games in games.json: ${games.length}`);
console.log(`\n✅ FULLY DONE (has HTML + image): ${fullyDone.length}`);
console.log(`📄 Has HTML file only: ${hasHTML.length}`);
console.log(`📸 Has image only: ${hasImage.length}`);
console.log(`📁 Has local files only: ${hasLocalFiles.length}`);
console.log(`❌ Missing everything: ${missingEverything.length}`);

console.log('\n' + '='.repeat(70));
console.log('FULLY DONE GAMES (HTML + Image):');
console.log('='.repeat(70));
if (fullyDone.length > 0) {
    fullyDone.slice(0, 50).forEach(game => {
        console.log(`  ✓ ${game.name} (ID: ${game.id}, dir: ${game.directory})`);
    });
    if (fullyDone.length > 50) {
        console.log(`  ... and ${fullyDone.length - 50} more`);
    }
} else {
    console.log('  (None found)');
}

console.log('\n' + '='.repeat(70));
console.log('GAMES WITH HTML FILES (need images):');
console.log('='.repeat(70));
if (hasHTML.length > 0) {
    hasHTML.slice(0, 30).forEach(game => {
        console.log(`  📄 ${game.name} (ID: ${game.id}, dir: ${game.directory})`);
    });
    if (hasHTML.length > 30) {
        console.log(`  ... and ${hasHTML.length - 30} more`);
    }
} else {
    console.log('  (None found)');
}

console.log('\n' + '='.repeat(70));
console.log('GAMES WITH IMAGES ONLY (need HTML files):');
console.log('='.repeat(70));
hasImage.slice(0, 20).forEach(game => {
    console.log(`  📸 ${game.name} (dir: ${game.directory})`);
});
if (hasImage.length > 20) {
    console.log(`  ... and ${hasImage.length - 20} more`);
}

// Save detailed report
const report = {
    summary: {
        total: games.length,
        fullyDone: fullyDone.length,
        hasHTML: hasHTML.length,
        hasImage: hasImage.length,
        hasLocalFiles: hasLocalFiles.length,
        missingEverything: missingEverything.length
    },
    fullyDone: fullyDone.map(g => ({ name: g.name, id: g.id, directory: g.directory, image: g.image })),
    hasHTML: hasHTML.map(g => ({ name: g.name, id: g.id, directory: g.directory, image: g.image })),
    hasImage: hasImage.map(g => ({ name: g.name, id: g.id, directory: g.directory, image: g.image })),
    hasLocalFiles: hasLocalFiles.map(g => ({ name: g.name, id: g.id, directory: g.directory, image: g.image })),
    missingEverything: missingEverything.slice(0, 100).map(g => ({ name: g.name, id: g.id, directory: g.directory, image: g.image }))
};

fs.writeFileSync(
    path.join(ROOT, 'game-status-report.json'),
    JSON.stringify(report, null, 2)
);

console.log('\n📄 Detailed report saved to: game-status-report.json');
console.log(`\n💡 Tip: Games with HTML files can be used immediately if you have the game assets!`);
