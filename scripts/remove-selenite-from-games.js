const fs = require('fs');
const path = require('path');

const gamesJsonPath = path.join(__dirname, '..', 'data', 'games.json');

function main() {
  const raw = fs.readFileSync(gamesJsonPath, 'utf8');
  const games = JSON.parse(raw);

  const originalLength = games.length;
  const kept = games.filter(g => !(typeof g.gameUrl === 'string' && g.gameUrl.startsWith('/non-semag/selenite/')));
  const removed = originalLength - kept.length;

  fs.writeFileSync(gamesJsonPath, JSON.stringify(kept, null, '\t'), 'utf8');
  console.log(`Removed ${removed} selenite games (non-semag/selenite) from games.json`);
}

main();

