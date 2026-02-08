const fs = require('fs');
const path = require('path');

const currentGamesPath = path.join(__dirname, '..', 'data', 'games.json');
const gitlabGamesPath = path.join(__dirname, '..', '..', 'semag-gitlab', 'selenite', 'data', 'games.json');

function main() {
  const current = JSON.parse(fs.readFileSync(currentGamesPath, 'utf8'));
  if (!fs.existsSync(gitlabGamesPath)) {
    console.error('semag-gitlab not found. Clone from https://gitlab.com/skysthelimit.dev/selenite first.');
    process.exit(1);
  }
  const gitlab = JSON.parse(fs.readFileSync(gitlabGamesPath, 'utf8'));

  const existingDirs = new Set(current.map(g => (g.directory || '').toLowerCase()).filter(Boolean));

  const semagEntries = gitlab
    .filter(g => typeof g.directory === 'string' && g.directory && !existingDirs.has(g.directory.toLowerCase()))
    .map(g => ({
      name: g.name,
      directory: g.directory,
      image: g.image || 'cover.png',
      source: 'semag',
      gameUrl: `/semag/${g.directory}/index.html`,
      imagePath: `/semag/${g.directory}/${g.image || 'cover.png'}`
    }));

  const merged = [...current, ...semagEntries];
  fs.writeFileSync(currentGamesPath, JSON.stringify(merged, null, '\t'), 'utf8');
  console.log(`Merged ${semagEntries.length} semag games into games.json (${merged.length} total)`);
}

main();
