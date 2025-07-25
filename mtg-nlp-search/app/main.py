from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.nlp import extract_filters
from app.scryfall import search_scryfall
from app.deck_analyzer import DeckAnalyzer
from typing import List

app = FastAPI(title="MTG NLP Search", description="Natural language search for Magic: The Gathering cards")

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

@app.get("/search")
def search(
    prompt: str = Query(..., description="Describe the kind of card you're looking for."),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page (1-100)")
):
    try:
        # Try to extract filters using NLP
        filters = extract_filters(prompt)
        print(f"Extracted filters: {filters}")
        
        # If OpenAI failed, create a basic filter from the prompt
        if not filters or (len(filters) == 1 and "raw_query" in filters):
            filters = {"raw_query": prompt}
            print(f"Using raw query: {prompt}")
        
        # Search Scryfall with pagination
        all_cards = search_scryfall(filters)
        total_results = len(all_cards)
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        cards = all_cards[start_idx:end_idx]
        
        total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
        
        print(f"Found {total_results} total cards, showing page {page}/{total_pages}")
        
        return {
            "prompt": prompt,
            "filters": filters,
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
        return {
            "prompt": prompt,
            "error": str(e),
            "results": [],
            "pagination": {
                "page": 1,
                "per_page": per_page,
                "total_results": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }

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
        return {
            "success": False,
            "error": str(e),
            "analysis": None
        }