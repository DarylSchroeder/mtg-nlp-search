# Sample Queries Refactor: URL Deep Linking Approach

## Current Issues
- Static examples in README don't demonstrate actual functionality
- Frontend hamburger menu requires clicks to test
- No easy way to share working examples
- Examples might become outdated if not tested regularly

## Proposed Refactor: Deep Link Sample Queries

### 1. API Endpoint for Sample Queries
Add a `/samples` endpoint that returns curated, tested sample queries:

```python
@app.get("/samples")
def get_sample_queries():
    """Return curated sample queries with deep links"""
    base_url = "https://rofellods-nlp-mtg.onrender.com"
    
    samples = [
        {
            "category": "Basic Searches",
            "queries": [
                {
                    "text": "1 mana counterspell",
                    "description": "Finds 1-cost counterspells like Abjure",
                    "url": f"{base_url}/?q=1%20mana%20counterspell",
                    "expected_results": 5
                },
                {
                    "text": "2 cmc rakdos instant", 
                    "description": "Finds 2-cost black/red instants",
                    "url": f"{base_url}/?q=2%20cmc%20rakdos%20instant",
                    "expected_results": 2
                }
            ]
        },
        {
            "category": "Guild Searches",
            "queries": [
                {
                    "text": "azorius removal",
                    "description": "White/blue removal spells",
                    "url": f"{base_url}/?q=azorius%20removal",
                    "expected_results": 15
                },
                {
                    "text": "simic creature 3 cmc",
                    "description": "3-cost green/blue creatures", 
                    "url": f"{base_url}/?q=simic%20creature%203%20cmc",
                    "expected_results": 25
                }
            ]
        },
        {
            "category": "Land Searches", 
            "queries": [
                {
                    "text": "fetchland",
                    "description": "All fetch lands",
                    "url": f"{base_url}/?q=fetchland",
                    "expected_results": 10
                },
                {
                    "text": "rakdos shockland",
                    "description": "Black/red shock lands",
                    "url": f"{base_url}/?q=rakdos%20shockland", 
                    "expected_results": 1
                }
            ]
        },
        {
            "category": "Commander Searches",
            "queries": [
                {
                    "text": "counterspell for my Chulane deck",
                    "description": "Counterspells legal in Bant colors",
                    "url": f"{base_url}/?q=counterspell%20for%20my%20Chulane%20deck",
                    "expected_results": 20
                },
                {
                    "text": "removal for Atraxa 2 cmc", 
                    "description": "2-cost removal for 4-color decks",
                    "url": f"{base_url}/?q=removal%20for%20Atraxa%202%20cmc",
                    "expected_results": 8
                }
            ]
        }
    ]
    
    return {
        "samples": samples,
        "total_categories": len(samples),
        "total_queries": sum(len(cat["queries"]) for cat in samples)
    }
```

### 2. Frontend Integration
Replace hamburger menu with dynamic sample loading:

```javascript
// Load samples from API
async function loadSampleQueries() {
    const response = await fetch('/samples');
    const data = await response.json();
    return data.samples;
}

// Render samples as clickable cards
function renderSampleQueries(samples) {
    const container = document.getElementById('samples-container');
    
    samples.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'sample-category';
        categoryDiv.innerHTML = `<h3>${category.category}</h3>`;
        
        category.queries.forEach(query => {
            const queryCard = document.createElement('div');
            queryCard.className = 'sample-query-card';
            queryCard.innerHTML = `
                <div class="query-text">"${query.text}"</div>
                <div class="query-description">${query.description}</div>
                <div class="query-meta">~${query.expected_results} results</div>
            `;
            
            // Make entire card clickable - navigates to deep link
            queryCard.onclick = () => window.location.href = query.url;
            
            categoryDiv.appendChild(queryCard);
        });
        
        container.appendChild(categoryDiv);
    });
}
```

### 3. README Update
Replace static examples with dynamic deep links:

```markdown
## Example Queries

Try these live examples (click to search):

### Basic Searches
- [1 mana counterspell](https://rofellods-nlp-mtg.onrender.com/?q=1%20mana%20counterspell) → 1-cost counterspells
- [2 cmc rakdos instant](https://rofellods-nlp-mtg.onrender.com/?q=2%20cmc%20rakdos%20instant) → Black/red 2-cost instants

### Guild Searches  
- [azorius removal](https://rofellods-nlp-mtg.onrender.com/?q=azorius%20removal) → White/blue removal
- [simic creature 3 cmc](https://rofellods-nlp-mtg.onrender.com/?q=simic%20creature%203%20cmc) → Green/blue 3-drops

### Land Searches
- [fetchland](https://rofellods-nlp-mtg.onrender.com/?q=fetchland) → All fetch lands
- [rakdos shockland](https://rofellods-nlp-mtg.onrender.com/?q=rakdos%20shockland) → Blood Crypt

### Commander Searches
- [counterspell for my Chulane deck](https://rofellods-nlp-mtg.onrender.com/?q=counterspell%20for%20my%20Chulane%20deck) → Bant counterspells
- [removal for Atraxa 2 cmc](https://rofellods-nlp-mtg.onrender.com/?q=removal%20for%20Atraxa%202%20cmc) → 2-cost 4-color removal

[View all sample queries →](https://rofellods-nlp-mtg.onrender.com/samples)
```

### 4. Testing Integration
Add sample query validation to test suite:

```bash
#!/bin/bash
# test_sample_queries.sh

echo "Testing sample queries..."

# Get samples from API
SAMPLES=$(curl -s "https://mtg-nlp-search.onrender.com/samples")

# Test each sample query
echo "$SAMPLES" | jq -r '.samples[].queries[] | "\(.text)|\(.expected_results)"' | while IFS='|' read -r query expected; do
    echo "Testing: $query"
    
    # URL encode query
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")
    
    # Test API
    result=$(curl -s "https://mtg-nlp-search.onrender.com/search?prompt=$encoded")
    actual=$(echo "$result" | jq '.pagination.total_results')
    
    if [ "$actual" -eq "$expected" ]; then
        echo "✅ $query: $actual results (expected $expected)"
    else
        echo "❌ $query: $actual results (expected $expected)"
    fi
done
```

## Benefits of This Approach

1. **Shareable Examples**: Each sample is a working deep link
2. **Always Current**: Samples are tested in CI/CD pipeline  
3. **Better UX**: Click to try instead of copy/paste
4. **Discoverable**: `/samples` endpoint for API consumers
5. **Maintainable**: Centralized sample management
6. **SEO Friendly**: Deep links are indexable
7. **Analytics Ready**: Can track which samples are most popular

## Implementation Priority

1. ✅ **Phase 1**: Add `/samples` API endpoint
2. **Phase 2**: Update README with deep links  
3. **Phase 3**: Replace frontend hamburger menu
4. **Phase 4**: Add sample query testing to CI/CD
