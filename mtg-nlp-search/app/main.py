from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.nlp import extract_filters
from app.scryfall import search_scryfall
from app.deck_analyzer import DeckAnalyzer
from app.commanders import commander_db
from typing import List
import asyncio
import datetime
import subprocess
import os

app = FastAPI(title="MTG NLP Search", description="Natural language search for Magic: The Gathering cards")

# Store server start time
SERVER_START_TIME = datetime.datetime.utcnow()

def get_git_commit_hash():
    """Get the current git commit hash"""
    try:
        # Try to get the commit hash from git
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'], 
            capture_output=True, 
            text=True, 
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to repo root
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]  # Short hash
        else:
            return "unknown"
    except Exception:
        return "unknown"

def get_git_branch():
    """Get the current git branch"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "unknown"
    except Exception:
        return "unknown"

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rofellods-nlp-mtg.onrender.com",
        "https://www.rofellods.com", 
        "http://localhost:8080",
        "http://localhost:3000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load commander database at server startup"""
    # Run in background to not block startup
    asyncio.create_task(load_commanders_background())

async def load_commanders_background():
    """Background task to load commanders with timeout and fallback"""
    try:
        import asyncio
        
        async def load_with_timeout():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, commander_db.load_commanders_at_startup)
        
        # 30 second timeout for the entire loading process
        try:
            success = await asyncio.wait_for(load_with_timeout(), timeout=30.0)
            
            if success:
                print("🎉 Commander database loaded successfully in background")
            else:
                print("⚠️  Commander database loaded with fallback")
                
        except asyncio.TimeoutError:
            print("⏰ Commander loading timed out after 30s, using fallback")
            commander_db._load_fallback_commanders()
            
    except Exception as e:
        print(f"❌ Commander loading failed: {e}")
        commander_db._load_fallback_commanders()

@app.get("/")
def read_root():
    return {
        "message": "MTG NLP Search API", 
        "commanders_loaded": commander_db.loaded,
        "commander_count": len(commander_db.commanders) if commander_db.loaded else 0
    }

@app.get("/debug-nlp")
def debug_nlp(prompt: str = Query(..., description="Debug NLP parsing")):
    """Debug endpoint to test NLP parsing directly"""
    try:
        from app.nlp import extract_filters
        filters = extract_filters(prompt)
        
        return {
            "prompt": prompt,
            "filters": filters,
            "debug": "Direct NLP call from API endpoint"
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "error": str(e),
            "debug": "Error in NLP parsing"
        }

@app.get("/search")
def search(
    prompt: str = Query(..., description="Describe the kind of card you're looking for."),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page (1-100)")
):
    try:
        # Try to extract filters using NLP
        filters = extract_filters(prompt)
        print(f"API: Extracted filters: {filters}")
        
        # If OpenAI failed, create a basic filter from the prompt
        if not filters or (len(filters) == 1 and "raw_query" in filters):
            filters = {"raw_query": prompt}
            print(f"API: Using raw query: {prompt}")
        
        # Calculate which Scryfall page we need
        # Scryfall uses 175 cards per page, our API uses configurable per_page
        scryfall_page = ((page - 1) * per_page) // 175 + 1
        
        # Search Scryfall with pagination
        search_result = search_scryfall(filters, scryfall_page)
        scryfall_cards = search_result["cards"]
        scryfall_query = search_result["query"]
        total_results = search_result.get("total_cards", len(scryfall_cards))
        
        print(f"API: Scryfall query: {scryfall_query}")
        print(f"API: Total results: {total_results}")
        print(f"API: Requested page {page}, fetching Scryfall page {scryfall_page}")
        print(f"API: Final filters: {filters}")
        
        # Calculate pagination within the Scryfall page
        scryfall_start_idx = ((page - 1) * per_page) % 175
        scryfall_end_idx = min(scryfall_start_idx + per_page, len(scryfall_cards))
        cards = scryfall_cards[scryfall_start_idx:scryfall_end_idx]
        
        # If we need more cards and there are more Scryfall pages, fetch the next page
        if len(cards) < per_page and scryfall_start_idx + per_page > 175:
            next_scryfall_page = scryfall_page + 1
            next_search_result = search_scryfall(filters, next_scryfall_page)
            next_cards = next_search_result["cards"]
            
            # Add remaining cards from next page
            remaining_needed = per_page - len(cards)
            cards.extend(next_cards[:remaining_needed])
            print(f"API: Fetched additional {len(next_cards[:remaining_needed])} cards from page {next_scryfall_page}")
        
        total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
        
        print(f"Found {total_results} total cards, showing page {page}/{total_pages}")
        
        return {
            "prompt": prompt,
            "filters": filters,
            "scryfall_query": scryfall_query,  # Include the actual Scryfall query
            "results": cards,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_results": total_results,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        error_str = str(e).lower()
        
        # Detect cold start / server warmup issues
        if ("timeout" in error_str or 
            "connection" in error_str or 
            "failed to establish" in error_str or
            "service unavailable" in error_str):
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail={
                    "error": "Server is warming up, please try again in a moment",
                    "error_type": "cold_start",
                    "retry_after": 10,
                    "prompt": prompt
                }
            )
        
        # Check if commanders are still loading
        if not commander_db.loaded:
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail={
                    "error": "Server is still loading data, please try again in a moment",
                    "error_type": "loading",
                    "retry_after": 5,
                    "prompt": prompt
                }
            )
        
        # General server errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": "server_error",
                "prompt": prompt
            }
        )

@app.post("/analyze-deck")
def analyze_deck(card_names: List[str]):
    """Analyze a deck list and suggest improvements"""
    try:
        analyzer = DeckAnalyzer()
        results = analyzer.analyze_deck_list(card_names)
        
        return {
            "success": True,
            "analysis": results
        }
    except Exception as e:
        print(f"Error in deck analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": "deck_analysis_error"
            }
        )

@app.get("/samples")
def get_sample_queries():
    """Return basic example queries for API documentation and testing"""
    return {
        "basic_examples": [
            "1 mana counterspell",
            "2 cmc rakdos instant", 
            "fetchland",
            "4 cost red creature"
        ],
        "guild_examples": [
            "boros instant",
            "dimir sorcery",
            "selesnya enchantment"
        ],
        "commander_examples": [
            "counterspell for my Chulane deck",
            "removal for Atraxa",
            "ramp for my Korvold deck"
        ],
        "land_examples": [
            "shockland",
            "triome",
            "fetchland"
        ],
        "note": "These are basic examples for API testing. Frontend should manage its own sample queries with UI-specific metadata."
    }

@app.get("/health-check")
def health_check():
    """Health check endpoint with deployment metadata"""
    current_time = datetime.datetime.utcnow()
    uptime_seconds = (current_time - SERVER_START_TIME).total_seconds()
    
    # Format uptime in a human-readable way
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    uptime_secs = int(uptime_seconds % 60)
    
    uptime_formatted = f"{uptime_hours}h {uptime_minutes}m {uptime_secs}s"
    
    # Detect if server is in cold start phase (first 60 seconds)
    is_cold_start = uptime_seconds < 60
    
    return {
        "status": "healthy",
        "timestamp": current_time.isoformat() + "Z",
        "server_start_time": SERVER_START_TIME.isoformat() + "Z",
        "uptime": {
            "seconds": int(uptime_seconds),
            "formatted": uptime_formatted
        },
        "deployment": {
            "git_commit": get_git_commit_hash(),
            "git_branch": get_git_branch(),
            "environment": "render" if os.environ.get("RENDER") else "local"
        },
        "services": {
            "commanders_loaded": commander_db.loaded,
            "commander_count": len(commander_db.commanders) if commander_db.loaded else 0,
            "ready_for_search": commander_db.loaded and not is_cold_start
        },
        "cold_start": is_cold_start,
        "version": "1.0.0"  # You can update this manually or read from a version file
    }

@app.get("/commanders")
def get_commanders(search: str = Query(None, description="Search commander names")):
    """Get commander information"""
    if not commander_db.loaded:
        return {
            "loaded": False,
            "message": "Commander database still loading, please try again in a moment"
        }
    
    if search:
        # Search for specific commanders
        results = commander_db.search_commanders(search, limit=20)
        return {
            "loaded": True,
            "query": search,
            "results": results,
            "total_commanders": len(commander_db.commanders)
        }
    else:
        # Return summary info
        return {
            "loaded": True,
            "total_commanders": len(commander_db.commanders),
            "sample_commanders": list(commander_db.commanders.keys())[:20],
            "message": "Use ?search=name to search for specific commanders"
        }

@app.get("/commanders/{commander_name}")
def get_commander_info(commander_name: str):
    """Get detailed info for a specific commander"""
    if not commander_db.loaded:
        return {"error": "Commander database still loading"}
    
    colors = commander_db.get_commander_colors(commander_name)
    info = commander_db.get_commander_info(commander_name)
    
    if colors:
        return {
            "name": commander_name,
            "color_identity": colors,
            "found": True,
            "card_info": info
        }
    else:
        return {
            "name": commander_name,
            "found": False,
            "suggestions": commander_db.search_commanders(commander_name, limit=5)
        }