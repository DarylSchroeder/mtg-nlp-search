# Architecture Refactor: Separation of Concerns

## Problem 1: Commander Implementation

### Current Issues
- Only 7 hardcoded commanders in `COMMANDERS` dict
- Missing popular commanders like Korvold, Muldrotha, etc.
- No systematic way to expand the list
- Manual maintenance required

### Solution: Dynamic Commander Lookup

```python
# mtg-nlp-search/app/commanders.py
import requests
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_commander_colors(commander_name: str) -> str:
    """
    Dynamically look up commander color identity from Scryfall
    Returns color identity string like 'WUBG' or None if not found
    """
    try:
        # Search for exact commander name
        response = requests.get(
            "https://api.scryfall.com/cards/named",
            params={"exact": commander_name}
        )
        
        if response.status_code == 200:
            card = response.json()
            # Check if it's a legendary creature (potential commander)
            if ("Legendary" in card.get("type_line", "") and 
                "Creature" in card.get("type_line", "")):
                return ''.join(card.get("color_identity", []))
        
        # Fallback: fuzzy search
        response = requests.get(
            "https://api.scryfall.com/cards/search",
            params={
                "q": f'"{commander_name}" is:commander',
                "order": "name"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                card = data["data"][0]  # Take first match
                return ''.join(card.get("color_identity", []))
                
    except Exception as e:
        print(f"Error looking up commander {commander_name}: {e}")
    
    return None

# Keep a small cache of popular commanders for performance
POPULAR_COMMANDERS = {
    'chulane': 'GWU',
    'atraxa': 'WUBG', 
    'korvold': 'BRG',  # Add missing ones
    'muldrotha': 'UBG',
    'edgar markov': 'RWB',
    'the ur-dragon': 'WUBRG',
    'alesha': 'RWB',
    'kenrith': 'WUBRG',
    'meren': 'BG',
    'krenko': 'R',
    'sisay': 'WG'
}

def extract_commander_colors(prompt_lower: str) -> tuple:
    """Extract commander color identity with fallback to API lookup"""
    
    # First check popular commanders cache
    for commander, colors in POPULAR_COMMANDERS.items():
        if commander in prompt_lower:
            return colors, False  # (colors, use_color_not_identity)
    
    # Dynamic lookup for unknown commanders
    # Extract potential commander names from phrases like "for my X deck"
    import re
    deck_patterns = [
        r'for my (\w+(?:\s+\w+)*) deck',
        r'in (\w+(?:\s+\w+)*) colors',
        r'(\w+(?:\s+\w+)*) commander'
    ]
    
    for pattern in deck_patterns:
        matches = re.findall(pattern, prompt_lower)
        for match in matches:
            colors = get_commander_colors(match.title())
            if colors:
                return colors, False
    
    return None, False
```

## Problem 2: Frontend Logic in API Layer

### Current Issues
- `/samples` endpoint contains UI concerns
- Frontend URL construction in backend
- Testing metadata mixed with API responses
- Tight coupling between frontend and backend

### Solution: Proper Separation

#### Backend: Pure API Endpoints
```python
# mtg-nlp-search/app/main.py - Keep API focused on data

@app.get("/search/examples")
def get_search_examples():
    """Return minimal example queries for API documentation"""
    return {
        "basic_examples": [
            "1 mana counterspell",
            "2 cmc rakdos instant", 
            "fetchland"
        ],
        "guild_examples": [
            "boros instant",
            "dimir sorcery"
        ],
        "commander_examples": [
            "counterspell for my Chulane deck",
            "removal for Atraxa"
        ],
        "land_examples": [
            "shockland",
            "triome"
        ]
    }

# Remove the complex /samples endpoint - move to frontend
```

#### Frontend: UI-Specific Sample Management
```javascript
// frontend/src/sampleQueries.js
export const SAMPLE_QUERIES = {
  categories: [
    {
      name: "Basic Searches",
      description: "Simple mana cost and type searches",
      queries: [
        {
          text: "2 cmc rakdos instant",
          description: "2-cost black/red instants",
          tags: ["guild", "instant", "rakdos"]
        },
        {
          text: "1 cmc blue instant", 
          description: "1-cost blue instants",
          tags: ["instant", "blue", "cantrip"]
        }
        // ... more queries
      ]
    }
    // ... more categories
  ]
};

// frontend/src/components/SampleQueries.jsx
export function SampleQueries({ onQuerySelect }) {
  const handleQueryClick = (queryText) => {
    // Update URL and trigger search
    const newUrl = `${window.location.pathname}?q=${encodeURIComponent(queryText)}`;
    window.history.pushState({ query: queryText }, '', newUrl);
    onQuerySelect(queryText);
  };

  return (
    <div className="sample-queries">
      {SAMPLE_QUERIES.categories.map(category => (
        <div key={category.name} className="category">
          <h3>{category.name}</h3>
          <p>{category.description}</p>
          <div className="queries-grid">
            {category.queries.map(query => (
              <button 
                key={query.text}
                onClick={() => handleQueryClick(query.text)}
                className="query-card"
              >
                <div className="query-text">"{query.text}"</div>
                <div className="query-description">{query.description}</div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

#### Testing: Separate Test Suite
```python
# tests/test_sample_queries.py
import requests
from frontend_samples import SAMPLE_QUERIES  # Import from frontend

def test_sample_queries():
    """Test that frontend sample queries work correctly"""
    base_url = "https://mtg-nlp-search.onrender.com"
    
    for category in SAMPLE_QUERIES["categories"]:
        for query in category["queries"]:
            response = requests.get(f"{base_url}/search", params={"prompt": query["text"]})
            assert response.status_code == 200
            
            data = response.json()
            results = data["pagination"]["total_results"]
            
            # Basic validation - should return some results
            assert results > 0, f"Query '{query['text']}' returned no results"
            
            print(f"✅ {query['text']}: {results} results")
```

## Benefits of This Refactor

### Commander System
1. **Scalable**: Automatically handles any commander via Scryfall API
2. **Accurate**: Always up-to-date with current commanders
3. **Performance**: LRU cache + popular commanders cache
4. **Maintainable**: No manual list maintenance

### Architecture
1. **Separation of Concerns**: API handles data, frontend handles UI
2. **Testable**: Clear boundaries for testing each layer
3. **Flexible**: Frontend can change sample queries without backend changes
4. **Cacheable**: Frontend samples can be cached/bundled
5. **Deployable**: Frontend and backend can be deployed independently

## Implementation Priority

1. **Phase 1**: Fix missing commanders (add Korvold to hardcoded list)
2. **Phase 2**: Implement dynamic commander lookup
3. **Phase 3**: Move sample queries to frontend
4. **Phase 4**: Update test suite for new architecture
