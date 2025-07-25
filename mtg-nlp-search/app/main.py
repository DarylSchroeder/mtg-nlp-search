from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from app.nlp import extract_filters
from app.scryfall import search_scryfall

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
def search(prompt: str = Query(..., description="Describe the kind of card you're looking for.")):
    try:
        # Try to extract filters using NLP
        filters = extract_filters(prompt)
        print(f"Extracted filters: {filters}")
        
        # If OpenAI failed, create a basic filter from the prompt
        if not filters or (len(filters) == 1 and "raw_query" in filters):
            filters = {"raw_query": prompt}
            print(f"Using raw query: {prompt}")
        
        # Search Scryfall
        cards = search_scryfall(filters)
        print(f"Found {len(cards)} cards")
        
        return {
            "prompt": prompt,
            "filters": filters,
            "results": cards[:10]  # Limit to first 10 results
        }
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        return {
            "prompt": prompt,
            "error": str(e),
            "results": []
        }