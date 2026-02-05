const fs = require('fs');
const path = require('path');

// Read zones.json from gn-math-assets
const zonesPath = path.join(__dirname, 'gn-math-assets', 'zones.json');
const zonesData = JSON.parse(fs.readFileSync(zonesPath, 'utf8'));

// Read current games.json
const gamesPath = path.join(__dirname, 'data', 'games.json');
const currentGames = JSON.parse(fs.readFileSync(gamesPath, 'utf8'));

// Create a map of existing game names (normalized for comparison)
const existingGamesMap = new Map();
currentGames.forEach(game => {
    const normalizedName = game.name.toLowerCase().trim();
    existingGamesMap.set(normalizedName, game);
});

// Function to slugify a name for directory
function slugify(text) {
    return text
        .toString()
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')
        .replace(/[^\w\-]+/g, '')
        .replace(/\-\-+/g, '-')
        .replace(/^-+/, '')
        .replace(/-+$/, '');
}

// Function to normalize game name for comparison
function normalizeName(name) {
    return name.toLowerCase().trim()
        .replace(/[^\w\s]/g, '')
        .replace(/\s+/g, ' ');
}

// Find games in zones.json that don't exist in current games.json
const newGames = [];
const skippedGames = [];

zonesData.forEach(zone => {
    // Skip suggestion/partner entries
    if (zone.id < 0 || !zone.name || zone.name.startsWith('[!]')) {
        return;
    }
    
    const normalizedName = normalizeName(zone.name);
    
    // Check if game already exists (by name)
    if (!existingGamesMap.has(normalizedName)) {
        // Extract cover image filename from cover URL
        let imagePath = 'cover.png'; // default
        if (zone.cover) {
            const coverMatch = zone.cover.match(/\/([^\/]+)$/);
            if (coverMatch) {
                imagePath = coverMatch[1];
            }
        }
        
        // Create directory name from game name
        const directory = slugify(zone.name);
        
        newGames.push({
            name: zone.name,
            image: imagePath,
            directory: directory
        });
    } else {
        skippedGames.push(zone.name);
    }
});

console.log(`Found ${newGames.length} new games to add`);
console.log(`Skipped ${skippedGames.length} games that already exist`);

// Merge new games with existing games
const allGames = [...currentGames, ...newGames];

// Sort by name
allGames.sort((a, b) => a.name.localeCompare(b.name));

// Write updated games.json
fs.writeFileSync(gamesPath, JSON.stringify(allGames, null, '\t'));

console.log(`\nUpdated games.json with ${allGames.length} total games`);
console.log(`\nNew games added:`);
newGames.forEach(game => {
    console.log(`  - ${game.name} (directory: ${game.directory}, image: ${game.image})`);
});

// Create a list of images to copy
const imagesToCopy = [];
const imgDir = path.join(__dirname, 'img');

// Ensure img directory exists
if (!fs.existsSync(imgDir)) {
    fs.mkdirSync(imgDir, { recursive: true });
}

newGames.forEach(game => {
    const zone = zonesData.find(z => normalizeName(z.name) === normalizeName(game.name));
    if (zone && zone.id !== undefined && zone.id >= 0) {
        // Try gn-math-covers first (primary source for cover images)
        const coversImage = path.join(__dirname, 'gn-math-covers', `${zone.id}.png`);
        if (fs.existsSync(coversImage)) {
            imagesToCopy.push({
                source: coversImage,
                dest: path.join(imgDir, game.image),
                game: game.name
            });
        } else {
            // Try to find image in numbered directories
            const numberedDir = path.join(__dirname, 'gn-math-assets', zone.id.toString());
            const coverInDir = path.join(numberedDir, 'cover.png');
            
            if (fs.existsSync(coverInDir)) {
                imagesToCopy.push({
                    source: coverInDir,
                    dest: path.join(imgDir, game.image),
                    game: game.name
                });
            } else {
                // Try root level image with ID
                const rootImage = path.join(__dirname, 'gn-math-assets', `${zone.id}.png`);
                if (fs.existsSync(rootImage)) {
                    imagesToCopy.push({
                        source: rootImage,
                        dest: path.join(imgDir, game.image),
                        game: game.name
                    });
                }
            }
        }
    }
});

console.log(`\nFound ${imagesToCopy.length} images to copy (out of ${newGames.length} new games)`);
if (imagesToCopy.length > 0) {
    imagesToCopy.forEach(img => {
        console.log(`  - Copying ${path.basename(img.source)} -> img/${path.basename(img.dest)}`);
    });
}

// Copy images
let copiedCount = 0;
imagesToCopy.forEach(img => {
    try {
        fs.copyFileSync(img.source, img.dest);
        console.log(`  ✓ Copied image for ${img.game}`);
        copiedCount++;
    } catch (error) {
        console.error(`  ✗ Failed to copy image for ${img.game}: ${error.message}`);
    }
});

if (imagesToCopy.length < newGames.length) {
    console.log(`\nNote: ${newGames.length - imagesToCopy.length} games don't have local images available.`);
    console.log(`You may need to download images from the cover URLs in zones.json or add them manually.`);
}

