# MTG NLP Search

A natural language search API for Magic: The Gathering cards using the Scryfall API.

## Features

- **Natural Language Parsing**: Search using plain English like "1 mana counterspell" or "fetchland"
- **Mana Cost Detection**: Automatically parses "2 mana", "3 cost", etc. into CMC filters
- **Color Identity**: Supports guild names (azorius, simic) and commander deck contexts
- **Card Types**: Recognizes creatures, instants, sorceries, lands, etc.
- **Effects**: Detects counterspells, ramp, removal, card draw, and more
- **Land Types**: Understands fetchlands, shocklands, triomes, etc.

## Quick Start

1. **Install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn requests
   ```

2. **Start the server:**
   ```bash
   cd mtg-nlp-search
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Test it:**
   ```bash
   curl -G "http://localhost:8000/search" --data-urlencode "prompt=1 mana counterspell"
   ```

## Example Queries

- `"1 mana counterspell"` → Finds 1-cost counterspells like Abjure
- `"azorius removal"` → Finds white/blue removal spells  
- `"fetchland"` → Finds fetch lands like Polluted Delta
- `"counterspell for my Chulane deck"` → Finds counterspells legal in GWU colors
- `"3 mana simic creature"` → Finds 3-cost green/blue creatures

## Testing

Run the simple test suite:

```bash
./run_tests.sh
```

## Deployment

### Render.com (Recommended)

The project is configured for easy deployment on Render.com:

1. **Connect your GitHub repo** to Render.com
2. **Create a new Web Service** from your repository
3. **Use the following settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
   - No environment variables needed (uses built-in NLP parsing)

The `render.yaml` file contains the complete configuration.

### Manual Deployment

For other platforms, the service runs on any Python environment with:
```bash
pip install fastapi uvicorn requests
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Key Fix

Fixed critical parsing issue where "mana" was incorrectly triggering ramp detection:
- **Before**: `"1 mana counterspell"` → `{"cmc":1,"effects":["counter","ramp"]}` ❌
- **After**: `"1 mana counterspell"` → `{"cmc":1,"effects":["counter"]}` ✅

## Architecture

- **FastAPI** backend with single `/search` endpoint
- **NLP Parser** extracts filters from natural language
- **Scryfall API** integration for card data
- **Simple testing** with vanilla bash/curl (no frameworks)
