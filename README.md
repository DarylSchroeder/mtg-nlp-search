# MTG NLP Search

A complete natural language search system for Magic: The Gathering cards with both API backend and web frontend.

## ⚠️ **Critical: Scryfall Color Syntax**
**COLOR, CMC, and COLORIDENTITY must use `=` operators, NOT `:` syntax!**

- `COLOR=R` → **exactly RED only** (mono-red cards)
- `COLOR>=R` → **has RED in it** (red + any other colors)  
- `COLOR<=R` → **red color identity** (same as COLORIDENTITY=R)
- `CMC=3` → **exactly 3 mana cost**
- `CMC>=3` → **3 or more mana cost**
- `CMC<=3` → **3 or less mana cost**

**Other fields** like `o:`, `type:`, `name:` still use `:` syntax.

**Examples:**
```python
# Individual colors use COLOR= (exact match)
"blue artifact" → COLOR=U type:artifact

# Guild names use COLOR<= (color identity)  
"azorius counterspell" → COLOR<=WU o:"counter target"

# Mana costs use CMC=
"3 mana red creature" → CMC=3 COLOR=R type:creature
```

## Repository Structure

This is the **backend API repository**. The complete system consists of two independent repositories in a unified workspace:

- **Backend API**: `DarylSchroeder/mtg-nlp-search` (this repository)
  - FastAPI backend with `/search`, `/analyze-deck`, and `/health-check` endpoints
  - Natural language processing for MTG card queries
  - Scryfall API integration
  - Deployed at: https://mtg-nlp-search.onrender.com

- **Frontend Web App**: `DarylSchroeder/rofellods-nlp-mtg` (sister repository at `../frontend`)
  - HTML/CSS/JavaScript web interface
  - Consumes the backend API endpoints
  - User-friendly search interface with card display
  - Deployed at: https://rofellods-nlp-mtg.onrender.com

**Unified Workspace**: Both repositories are organized under `/root/code/mtg-nlp-app/` for unified development while maintaining independent git history and deployment.

## Features

### 🔍 **Natural Language Search**
- **Smart Parsing**: Search using plain English like "1 mana counterspell" or "fetchland"
- **Mana Cost Detection**: Automatically parses "2 mana", "3 cost", "1 cmc", etc. into CMC filters
- **Color Identity**: Supports guild names (azorius, simic) and commander deck contexts
- **Card Types**: Recognizes creatures, instants, sorceries, lands, etc.
- **Effects**: Detects counterspells, ramp, removal, card draw, and more
- **Land Types**: Understands fetchlands, shocklands, triomes, etc.

### 🃏 **Deck Analysis** (NEW!)
- **Deck List Parsing**: Import standard MTG deck formats with set codes and collector numbers
- **Power Level Analysis**: Identifies underpowered cards using EDHREC rankings and efficiency metrics
- **Smart Suggestions**: Recommends better alternatives for removal, counterspells, and card draw
- **Format Awareness**: Tailored suggestions for Commander, Standard, and other formats
- **Comprehensive Reports**: Detailed analysis with improvement reasons and statistics

### ⚡ **Server Warm-up Indicator** (NEW!)
- **Cold Start Detection**: Automatically detects when serverless deployment is warming up
- **User-Friendly Messaging**: Shows "Server warming up..." after 5 seconds of waiting
- **Seamless Integration**: Works with any frontend implementation
- **No Configuration**: Automatically handles Render.com and similar serverless platforms

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

## API Endpoints

### `/search` - Natural Language Card Search
```bash
curl -G "http://localhost:8000/search" --data-urlencode "prompt=1 mana counterspell"
```

### `/analyze-deck` - Deck Analysis
```bash
curl -X POST "http://localhost:8000/analyze-deck" \
  -H "Content-Type: application/json" \
  -d '["Murder", "Cancel", "Lightning Bolt"]'
```

### `/health-check` - Server Health & Deployment Info (NEW!)
```bash
curl "http://localhost:8000/health-check"
```
Returns server metadata including:
- Server start time and uptime
- Git commit hash and branch
- Commander database status
- Environment information

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

- **FastAPI** backend with `/search` and `/analyze-deck` endpoints
- **NLP Parser** extracts filters from natural language
- **Deck Analyzer** identifies underpowered cards and suggests improvements
- **Scryfall API** integration for card data and EDHREC rankings
- **Simple testing** with vanilla bash/curl (no frameworks)
