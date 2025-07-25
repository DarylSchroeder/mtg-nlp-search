/**
 * Server Warm-up Indicator for MTG NLP Search
 * 
 * Shows "Server warming up..." message when search takes > 5 seconds
 * This handles serverless cold starts on Render.com and similar platforms
 */

class ServerWarmupIndicator {
    constructor() {
        this.warmupTimer = null;
        this.isWarmupShown = false;
    }

    /**
     * Start the warm-up timer when a search begins
     * @param {HTMLElement} searchIndicator - The "Searching cards..." element
     */
    startWarmupTimer(searchIndicator) {
        // Clear any existing timer
        this.clearWarmupTimer();
        
        // Set timer for 5 seconds
        this.warmupTimer = setTimeout(() => {
            if (searchIndicator && !this.isWarmupShown) {
                this.showWarmupMessage(searchIndicator);
            }
        }, 5000);
    }

    /**
     * Show the server warm-up message
     * @param {HTMLElement} searchIndicator - The search indicator element
     */
    showWarmupMessage(searchIndicator) {
        this.isWarmupShown = true;
        
        // Update the search indicator text
        const originalText = searchIndicator.textContent;
        searchIndicator.innerHTML = `
            <div class="warmup-message">
                <div class="spinner"></div>
                <div class="warmup-text">
                    <div>Server warming up...</div>
                    <div class="warmup-subtext">This may take a moment after inactivity</div>
                </div>
            </div>
        `;
        
        // Add CSS for the warm-up indicator
        this.addWarmupStyles();
    }

    /**
     * Clear the warm-up timer and reset state
     */
    clearWarmupTimer() {
        if (this.warmupTimer) {
            clearTimeout(this.warmupTimer);
            this.warmupTimer = null;
        }
        this.isWarmupShown = false;
    }

    /**
     * Add CSS styles for the warm-up indicator
     */
    addWarmupStyles() {
        // Check if styles already exist
        if (document.getElementById('warmup-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'warmup-styles';
        style.textContent = `
            .warmup-message {
                display: flex;
                align-items: center;
                gap: 12px;
                color: #666;
                font-size: 14px;
            }
            
            .warmup-text {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .warmup-subtext {
                font-size: 12px;
                color: #888;
                font-style: italic;
            }
            
            .spinner {
                width: 20px;
                height: 20px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #3498db;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Usage example for integration with existing search functionality:
/*
const warmupIndicator = new ServerWarmupIndicator();

function performSearch(query) {
    const searchIndicator = document.getElementById('search-indicator');
    
    // Show initial "Searching cards..." message
    searchIndicator.textContent = 'Searching cards...';
    searchIndicator.style.display = 'block';
    
    // Start the warm-up timer
    warmupIndicator.startWarmupTimer(searchIndicator);
    
    // Perform the actual search
    fetch(`/search?prompt=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            // Clear the warm-up timer on success
            warmupIndicator.clearWarmupTimer();
            
            // Hide the search indicator
            searchIndicator.style.display = 'none';
            
            // Display results
            displayResults(data);
        })
        .catch(error => {
            // Clear the warm-up timer on error
            warmupIndicator.clearWarmupTimer();
            
            // Show error message
            searchIndicator.textContent = 'Search failed. Please try again.';
            console.error('Search error:', error);
        });
}
*/

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ServerWarmupIndicator;
}

// Make available globally for direct HTML usage
if (typeof window !== 'undefined') {
    window.ServerWarmupIndicator = ServerWarmupIndicator;
}
