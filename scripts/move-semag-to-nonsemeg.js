const fs = require('fs');
const path = require('path');

const gamesJsonPath = path.join(__dirname, '..', 'data', 'games.json');

function main() {
  const raw = fs.readFileSync(gamesJsonPath, 'utf8');
  const games = JSON.parse(raw);

  let updatedCount = 0;

  for (const game of games) {
    if (game.source === 'semag') {
      game.source = 'non-semag';
      if (typeof game.gameUrl === 'string' && game.gameUrl.startsWith('/semag/')) {
        game.gameUrl = game.gameUrl.replace('/semag/', '/non-semag/selenite/');
      }
      if (typeof game.imagePath === 'string' && game.imagePath.startsWith('/semag/')) {
        game.imagePath = game.imagePath.replace('/semag/', '/non-semag/selenite/');
      }
      updatedCount++;
    }
  }

  fs.writeFileSync(gamesJsonPath, JSON.stringify(games, null, '\t'), 'utf8');
  console.log(`Updated ${updatedCount} semag entries to non-semag/selenite`);
}

main();

