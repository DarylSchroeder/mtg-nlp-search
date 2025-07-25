import requests
import urllib.parse
import time

def build_query(filters: dict) -> str:
    if "raw_query" in filters:
        # Try to convert common natural language patterns to Scryfall syntax
        raw = filters["raw_query"].lower()
        
        # Handle "X mana instant" patterns
        if "mana instant" in raw:
            # Extract number from patterns like "2 mana instant"
            words = raw.split()
            for i, word in enumerate(words):
                if word.isdigit() and i + 1 < len(words) and words[i + 1] == "mana":
                    return f"cmc:{word} type:instant"
        
        # Handle "instant" queries
        if "instant" in raw and "mana" in raw:
            # Try to extract mana cost
            words = raw.split()
            for word in words:
                if word.isdigit():
                    return f"cmc:{word} type:instant"
        
        # If we can't parse it, try a basic text search
        return raw

    parts = []
    if "cmc" in filters:
        parts.append(f"cmc:{filters['cmc']}")
    if "type" in filters:
        parts.append(f"type:{filters['type']}")
    if "effects" in filters:
        for effect in filters["effects"]:
            parts.append(f'o:"{effect}"')
    
    # If no specific filters, return empty (will cause 404, but that's better than invalid syntax)
    if not parts:
        return "type:instant"  # Default fallback
    
    return " ".join(parts)

def search_scryfall(filters: dict):
    query = build_query(filters)
    
    # URL encode the query
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}"
    
    # Set proper headers as required by Scryfall API
    headers = {
        'User-Agent': 'MTG-NLP-Search/1.0 (https://github.com/DarylSchroeder/mtg-nlp-search)',
        'Accept': 'application/json'
    }
    
    try:
        # Add a small delay to respect rate limits (Scryfall recommends 50-100ms)
        time.sleep(0.1)
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        elif response.status_code == 404:
            # No cards found - try a more generic search
            print(f"No results for query: {query}")
            return []
        else:
            print(f"Scryfall API error: {response.status_code} - {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []