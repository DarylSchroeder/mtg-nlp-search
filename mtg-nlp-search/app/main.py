from fastapi import FastAPI, Query
from app.nlp import extract_filters
from app.scryfall import search_scryfall

app = FastAPI(title="MTG NLP Search", description="Natural language search for Magic: The Gathering cards")

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