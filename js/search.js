// Complete search functionality rewrite
(function() {
    'use strict';
    
    var searchInitialized = false;
    
    // Main search function
    function performSearch() {
        var searchInput = document.getElementById('gamesearch');
        if (!searchInput) {
            console.log('Search input not found');
            return;
        }
        
        var searchTerm = (searchInput.value || '').trim().toUpperCase();
        var gamesContainer = document.getElementById('games');
        
        if (!gamesContainer) {
            console.log('Games container not found');
            return;
        }
        
        var allGames = gamesContainer.querySelectorAll('.game');
        var suggestCard = gamesContainer.querySelector('.suggest');
        
        console.log('Searching for: "' + searchTerm + '", found ' + allGames.length + ' games');
        
        // If search is empty, show everything
        if (searchTerm === '') {
            if (suggestCard) {
                suggestCard.style.removeProperty('display');
                suggestCard.removeAttribute('hidden');
            }
            allGames.forEach(function(game) {
                // Remove search classes and inline styles
                game.classList.remove('search-hidden', 'search-visible');
                game.style.removeProperty('display');
                game.style.removeProperty('visibility');
                game.style.removeProperty('opacity');
                game.removeAttribute('hidden');
            });
            return;
        }
        
        // Hide suggest card when searching
        if (suggestCard) {
            suggestCard.style.display = 'none';
        }
        
        // Search through games
        var matchCount = 0;
        allGames.forEach(function(game) {
            // Get game name from h1
            var h1 = game.querySelector('h1');
            var gameName = h1 ? (h1.textContent || h1.innerText || '').trim().toUpperCase() : '';
            
            // Get game ID
            var gameId = (game.id || '').toUpperCase();
            
            // Check for matches
            var matches = false;
            if (gameName && gameName.indexOf(searchTerm) !== -1) {
                matches = true;
            }
            if (!matches && gameId && gameId.indexOf(searchTerm) !== -1) {
                matches = true;
            }
            
            // Show or hide - try direct inline style override with maximum specificity
            if (matches) {
                // Use setProperty with !important flag for maximum override
                game.style.setProperty('display', 'block', 'important');
                game.style.setProperty('visibility', 'visible', 'important');
                game.style.setProperty('opacity', '1', 'important');
                
                // Also add/remove classes for CSS rules
                game.classList.remove('search-hidden');
                game.classList.add('search-visible');
                game.removeAttribute('hidden');
                
                // Force a reflow to ensure styles are applied
                game.offsetHeight;
                
                matchCount++;
                
                // Debug: Check if it's actually visible after setting
                var computed = window.getComputedStyle(game);
                if (computed.display === 'none') {
                    console.error('FAILED to show game:', game.id || gameName, 'Computed display:', computed.display);
                }
            } else {
                // Hide with !important
                game.style.setProperty('display', 'none', 'important');
                game.classList.add('search-hidden');
                game.classList.remove('search-visible');
            }
        });
        
        console.log('Search complete: ' + matchCount + ' matches found out of ' + allGames.length + ' total games');
        
        // Debug: Check actual visibility of matched games
        if (matchCount > 0) {
            var actuallyVisible = 0;
            allGames.forEach(function(g) {
                if (g.classList.contains('search-visible')) {
                    var computed = window.getComputedStyle(g);
                    if (computed.display !== 'none') {
                        actuallyVisible++;
                    } else {
                        console.warn('Game marked visible but display is none:', g.id || g.querySelector('h1')?.textContent);
                    }
                }
            });
            console.log('Actually visible games: ' + actuallyVisible + ' / ' + matchCount + ' matched');
        }
    }
    
    // Make search function globally available
    window.searchGames = performSearch;
    
    // Initialize search event listeners
    function initSearchListeners() {
        var searchInput = document.getElementById('gamesearch');
        if (!searchInput) {
            return false;
        }
        
        // Remove any existing listeners by cloning the element
        var newInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newInput, searchInput);
        
        // Add fresh event listeners
        newInput.addEventListener('input', performSearch);
        newInput.addEventListener('keyup', performSearch);
        newInput.addEventListener('keydown', performSearch);
        newInput.addEventListener('paste', function() {
            setTimeout(performSearch, 10);
        });
        
        // Handle URL parameters
        var urlParams = new URLSearchParams(window.location.search);
        var queryParam = urlParams.get('q');
        if (queryParam) {
            newInput.value = queryParam;
            setTimeout(performSearch, 100);
            urlParams.delete('q');
            var newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
            window.history.replaceState({}, document.title, newUrl);
        }
        
        console.log('Search listeners initialized');
        searchInitialized = true;
        return true;
    }
    
    // Initialize when DOM is ready
    function tryInit() {
        if (initSearchListeners()) {
            return true;
        }
        return false;
    }
    
    // Multiple initialization attempts
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(tryInit, 50);
            setTimeout(tryInit, 200);
            setTimeout(tryInit, 500);
        });
    } else {
        setTimeout(tryInit, 50);
        setTimeout(tryInit, 200);
        setTimeout(tryInit, 500);
    }
    
    // Also hook into games loading completion
    if (typeof jQuery !== 'undefined') {
        jQuery(document).ready(function($) {
            // Re-initialize after games load
            var originalLoadGames = window.loadGames;
            if (typeof originalLoadGames === 'undefined') {
                // Try to hook into the games.js loadGames function
                setTimeout(function() {
                    if (!searchInitialized) {
                        tryInit();
                    }
                    // Re-run search after games are loaded
                    setTimeout(performSearch, 100);
                }, 1000);
            }
        });
    }
    
    // Expose function to be called after games load
    window.reinitializeSearch = function() {
        if (!searchInitialized) {
            tryInit();
        }
        setTimeout(performSearch, 50);
    };
    
})();
