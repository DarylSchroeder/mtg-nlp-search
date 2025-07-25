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

## Key Fix

Fixed critical parsing issue where "mana" was incorrectly triggering ramp detection:
- **Before**: `"1 mana counterspell"` → `{"cmc":1,"effects":["counter","ramp"]}` ❌
- **After**: `"1 mana counterspell"` → `{"cmc":1,"effects":["counter"]}` ✅

## Architecture

- **FastAPI** backend with single `/search` endpoint
- **NLP Parser** extracts filters from natural language
- **Scryfall API** integration for card data
- **Simple testing** with vanilla bash/curl (no frameworks)
