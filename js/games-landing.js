// Games Landing Page Script
const GAMES_BASE_URL = window.location.origin;
let gamelist = [];

// Load games data and redirect to random game
function redirectToRandomGame() {
    if (gamelist.length > 0) {
        const randomGame = gamelist[Math.floor(Math.random() * gamelist.length)];
        const gameData = [randomGame.directory, randomGame.image, randomGame.name];
        const encoded = btoa(encodeURIComponent(JSON.stringify(gameData)));
        window.location.href = "loader.html#" + encoded;
    } else {
        // Load games first
        fetch("/data/games.json")
            .then(response => response.json())
            .then(data => {
                gamelist = data;
                const randomGame = gamelist[Math.floor(Math.random() * gamelist.length)];
                const gameData = [randomGame.directory, randomGame.image, randomGame.name];
                const encoded = btoa(encodeURIComponent(JSON.stringify(gameData)));
                window.location.href = "loader.html#" + encoded;
            })
            .catch(error => {
                console.error("Error loading games:", error);
                alert("Failed to load games. Please try again.");
            });
    }
}

// Load games count for stats
document.addEventListener("DOMContentLoaded", function() {
    fetch("/data/games.json")
        .then(response => response.json())
        .then(data => {
            gamelist = data;
            const gamesCount = data.length;
            
            // Update games count in stats
            const gamesStat = document.getElementById("games-count");
            if (gamesStat) {
                gamesStat.textContent = gamesCount;
            }
            
            // Get starred games count
            const starredGames = getCookie("starred");
            let starredCount = 0;
            if (starredGames) {
                try {
                    starredCount = JSON.parse(decodeURIComponent(starredGames)).length;
                } catch (e) {
                    starredCount = 0;
                }
            }
            
            const starredStat = document.getElementById("starred-count");
            if (starredStat) {
                starredStat.textContent = starredCount;
            }
        })
        .catch(error => console.error("Error loading games data:", error));
});

// Cookie helper function
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

