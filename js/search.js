// Simple and reliable search functionality
(function() {
    'use strict';
    
    // Global search state
    window.searchActive = false;
    
    // Search function
    window.searchGames = function() {
        var searchInput = document.getElementById('gamesearch');
        if (!searchInput) {
            return;
        }
        
        var searchTerm = searchInput.value.trim().toUpperCase();
        var gamesContainer = document.getElementById('games');
        if (!gamesContainer) {
            return;
        }
        
        var suggestCard = gamesContainer.querySelector('.suggest');
        var allGames = gamesContainer.querySelectorAll('.game');
        
        // If search is empty, show all games
        if (searchTerm === '') {
            window.searchActive = false;
            if (suggestCard) {
                suggestCard.style.display = '';
            }
            allGames.forEach(function(game) {
                game.style.display = '';
            });
            return;
        }
        
        // Search is active
        window.searchActive = true;
        
        // Hide suggest card
        if (suggestCard) {
            suggestCard.style.display = 'none';
        }
        
        // Search through games
        var matchCount = 0;
        allGames.forEach(function(game) {
            // Get game name from h1 element
            var gameTitle = game.querySelector('h1');
            var gameName = gameTitle ? gameTitle.textContent.toUpperCase() : '';
            
            // Get game ID
            var gameId = game.id ? game.id.toUpperCase() : '';
            
            // Check if search term matches
            var matches = false;
            if (gameName && gameName.indexOf(searchTerm) !== -1) {
                matches = true;
            } else if (gameId && gameId.indexOf(searchTerm) !== -1) {
                matches = true;
            }
            
            // Show or hide game
            if (matches) {
                game.style.display = '';
                matchCount++;
            } else {
                game.style.display = 'none';
            }
        });
        
        console.log('Search for "' + searchTerm + '" found ' + matchCount + ' matches');
    };
    
    // Initialize search when page loads
    function initializeSearch() {
        var searchInput = document.getElementById('gamesearch');
        if (searchInput) {
            // Handle URL parameters
            var urlParams = new URLSearchParams(window.location.search);
            var queryParam = urlParams.get('q');
            if (queryParam) {
                searchInput.value = queryParam;
                window.searchGames();
                urlParams.delete('q');
                var newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
                window.history.replaceState({}, document.title, newUrl);
            }
            
            // Add event listeners
            searchInput.addEventListener('input', window.searchGames);
            searchInput.addEventListener('keyup', window.searchGames);
            searchInput.addEventListener('change', window.searchGames);
            
            console.log('Search initialized');
            return true;
        }
        return false;
    }
    
    // Try to initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initializeSearch, 100);
        });
    } else {
        // DOM is already ready
        setTimeout(initializeSearch, 100);
    }
    
    // Also try with jQuery if available (for compatibility)
    if (typeof jQuery !== 'undefined') {
        jQuery(document).ready(function($) {
            setTimeout(function() {
                if (!initializeSearch()) {
                    // Retry after games load
                    setTimeout(initializeSearch, 500);
                }
            }, 100);
        });
    }
})();
