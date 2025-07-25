import requests

def build_query(filters: dict) -> str:
    if "raw_query" in filters:
        return filters["raw_query"]

    parts = []
    if "cmc" in filters:
        parts.append(f"cmc={filters['cmc']}")
    if "type" in filters:
        parts.append(f"type:{filters['type']}")
    if "effects" in filters:
        for effect in filters["effects"]:
            parts.append(f'o:"{effect}"')
    return "+".join(parts)

def search_scryfall(filters: dict):
    query = build_query(filters)
    url = f"https://api.scryfall.com/cards/search?q={query}"
    res = requests.get(url)
    return res.json().get("data", [])