from fastapi import FastAPI, Query
from app.nlp import extract_filters
from app.scryfall import search_scryfall

app = FastAPI()

@app.get("/search")
def search(prompt: str = Query(..., description="Describe the kind of card you're looking for.")):
    filters = extract_filters(prompt)
    cards = search_scryfall(filters)
    return {"filters": filters, "results": cards}