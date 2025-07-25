/**
 * Frontend JavaScript for Sample Queries with URL Navigation
 * 
 * This replaces the hamburger menu approach with dynamic sample loading
 * and proper URL navigation instead of just filling the search field.
 */

class SampleQueriesManager {
    constructor(apiBaseUrl = '') {
        this.apiBaseUrl = apiBaseUrl;
        this.samples = null;
    }

    /**
     * Load sample queries from the API
     */
    async loadSamples() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/samples`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            this.samples = await response.json();
            return this.samples;
        } catch (error) {
            console.error('Failed to load sample queries:', error);
            return null;
        }
    }

    /**
     * Navigate to a sample query (updates URL and triggers search)
     * This is the key improvement - we navigate instead of just filling the field
     */
    navigateToSample(queryText) {
        const encodedQuery = encodeURIComponent(queryText);
        const newUrl = `${window.location.origin}${window.location.pathname}?q=${encodedQuery}`;
        
        // Update URL and trigger search
        window.history.pushState({ query: queryText }, '', newUrl);
        
        // Trigger search (assuming there's a global search function)
        if (typeof window.performSearch === 'function') {
            window.performSearch(queryText);
        } else {
            // Fallback: reload page with new URL
            window.location.href = newUrl;
        }
    }

    /**
     * Render sample queries as clickable cards
     */
    renderSamples(containerId) {
        if (!this.samples) {
            console.error('No samples loaded. Call loadSamples() first.');
            return;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        container.innerHTML = ''; // Clear existing content

        // Add header
        const header = document.createElement('div');
        header.className = 'samples-header';
        header.innerHTML = `
            <h2>Try These Sample Searches</h2>
            <p>Click any example to search immediately</p>
        `;
        container.appendChild(header);

        // Render each category
        this.samples.samples.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'sample-category';
            
            const categoryHeader = document.createElement('h3');
            categoryHeader.textContent = category.category;
            categoryHeader.className = 'category-title';
            categoryDiv.appendChild(categoryHeader);

            const categoryDesc = document.createElement('p');
            categoryDesc.textContent = category.description;
            categoryDesc.className = 'category-description';
            categoryDiv.appendChild(categoryDesc);

            const queriesGrid = document.createElement('div');
            queriesGrid.className = 'queries-grid';

            category.queries.forEach(query => {
                const queryCard = this.createQueryCard(query);
                queriesGrid.appendChild(queryCard);
            });

            categoryDiv.appendChild(queriesGrid);
            container.appendChild(categoryDiv);
        });
    }

    /**
     * Create a clickable query card
     */
    createQueryCard(query) {
        const card = document.createElement('div');
        card.className = 'sample-query-card';
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        
        card.innerHTML = `
            <div class="query-text">"${query.text}"</div>
            <div class="query-description">${query.description}</div>
            <div class="query-meta">
                <span class="expected-results">${query.expected_min}-${query.expected_max} results</span>
                <div class="query-tags">
                    ${query.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
        `;

        // Add click handler for navigation
        const handleClick = () => {
            this.navigateToSample(query.text);
        };

        card.addEventListener('click', handleClick);
        card.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleClick();
            }
        });

        // Add hover effects
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-2px)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });

        return card;
    }

    /**
     * Render samples in a compact horizontal format (for homepage)
     */
    renderCompactSamples(containerId, maxQueries = 6) {
        if (!this.samples) return;

        const container = document.getElementById(containerId);
        if (!container) return;

        // Get a mix of queries from different categories
        const allQueries = [];
        this.samples.samples.forEach(category => {
            allQueries.push(...category.queries.map(q => ({...q, category: category.category})));
        });

        // Take first maxQueries
        const selectedQueries = allQueries.slice(0, maxQueries);

        container.innerHTML = `
            <h3>Popular Searches</h3>
            <div class="compact-queries">
                ${selectedQueries.map(query => `
                    <button class="compact-query-btn" onclick="sampleManager.navigateToSample('${query.text}')">
                        ${query.text}
                    </button>
                `).join('')}
            </div>
        `;
    }
}

/**
 * CSS Styles for Sample Queries (add to your stylesheet)
 */
const SAMPLE_QUERIES_CSS = `
.samples-header {
    text-align: center;
    margin-bottom: 2rem;
}

.sample-category {
    margin-bottom: 2rem;
    padding: 1rem;
    border-radius: 8px;
    background: #f8f9fa;
}

.category-title {
    color: #2c3e50;
    margin-bottom: 0.5rem;
}

.category-description {
    color: #6c757d;
    margin-bottom: 1rem;
    font-style: italic;
}

.queries-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
}

.sample-query-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.sample-query-card:hover {
    border-color: #007bff;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.query-text {
    font-weight: bold;
    color: #007bff;
    margin-bottom: 0.5rem;
    font-family: monospace;
}

.query-description {
    color: #495057;
    margin-bottom: 0.75rem;
    line-height: 1.4;
}

.query-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
}

.expected-results {
    color: #28a745;
    font-weight: 500;
}

.query-tags {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
}

.tag {
    background: #e9ecef;
    color: #495057;
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
}

.compact-queries {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.compact-query-btn {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 20px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: monospace;
}

.compact-query-btn:hover {
    background: #007bff;
    color: white;
    border-color: #007bff;
}

@media (max-width: 768px) {
    .queries-grid {
        grid-template-columns: 1fr;
    }
    
    .query-meta {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
}
`;

// Initialize the sample manager
const sampleManager = new SampleQueriesManager();

// Auto-load samples when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    await sampleManager.loadSamples();
    
    // Auto-render if samples container exists
    if (document.getElementById('samples-container')) {
        sampleManager.renderSamples('samples-container');
    }
    
    // Auto-render compact version if container exists
    if (document.getElementById('compact-samples')) {
        sampleManager.renderCompactSamples('compact-samples');
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SampleQueriesManager, SAMPLE_QUERIES_CSS };
}
