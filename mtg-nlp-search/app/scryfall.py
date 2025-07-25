import requests
import urllib.parse
import time
import re

def build_query(filters: dict) -> str:
    """Build Scryfall query from extracted filters"""
    
    # If we have a direct scryfall query, use it
    if "scryfall_query" in filters:
        return filters["scryfall_query"]
    
    # If we have a raw query, try to parse it better
    if "raw_query" in filters:
        return parse_raw_query(filters["raw_query"])
    
    # Build query from structured filters
    parts = []
    
    # Mana cost
    if "cmc" in filters:
        parts.append(f"cmc:{filters['cmc']}")
    
    # Card type
    if "type" in filters:
        parts.append(f"type:{filters['type']}")
    
    # Color identity (regular - allows subset matching)
    if "coloridentity" in filters:
        parts.append(f"coloridentity:{filters['coloridentity']}")
    
    # Color identity exact (requires exact match)
    if "coloridentity_exact" in filters:
        parts.append(f"coloridentity={filters['coloridentity_exact']}")
    
    # Power and toughness
    if "power" in filters:
        parts.append(f"power:{filters['power']}")
    if "toughness" in filters:
        parts.append(f"toughness:{filters['toughness']}")
    
    # Effects (search in oracle text)
    if "effects" in filters:
        for effect in filters["effects"]:
            effect_query = build_effect_query(effect)
            if effect_query:
                parts.append(effect_query)
    
    # If no parts, return a basic search
    if not parts:
        return "type:creature"  # Default fallback
    
    return " ".join(parts)

def build_effect_query(effect: str) -> str:
    """Convert effect keywords to Scryfall oracle text searches"""
    effect_mappings = {
        'counter': '(o:"counter target" OR o:"counter that" OR o:"counter it" OR o:"counter all" OR o:"counter each")',
        'draw': 'o:"draw"',
        'removal': '(o:"destroy target" OR o:"exile target")',
        'ramp': '(o:"search your library" AND o:"land")',
        'token': 'o:"create"',
        'damage': 'o:"damage"',
        'life': 'o:"gain" AND o:"life"',
        'flying': 'o:"flying"',
        'vigilance': 'o:"vigilance"',
        'trample': 'o:"trample"',
        'haste': 'o:"haste"',
        'defender': 'o:"defender"',
        'flashback': 'o:"flashback"',
        'tap': 'o:"tap"'
    }
    
    return effect_mappings.get(effect, f'o:"{effect}"')

def parse_raw_query(raw_query: str) -> str:
    """Enhanced raw query parser for common Magic patterns"""
    query = raw_query.lower().strip()
    
    # Handle power/toughness patterns
    pt_match = re.search(r'(\d+)/(\d+)', query)
    if pt_match:
        power = pt_match.group(1)
        toughness = pt_match.group(2)
        
        # Look for creature type
        creature_types = ['dinosaur', 'dragon', 'angel', 'demon', 'beast', 'elemental', 'zombie', 'goblin']
        for creature_type in creature_types:
            if creature_type in query:
                return f"power:{power} toughness:{toughness} type:{creature_type}"
        
        return f"power:{power} toughness:{toughness} type:creature"
    
    # Handle "X mana Y" patterns
    mana_match = re.search(r'(\d+|zero|one|two|three|four|five)\s+mana\s+(\w+)', query)
    if mana_match:
        mana_word = mana_match.group(1)
        card_type = mana_match.group(2)
        
        # Convert word numbers to digits
        word_to_num = {'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5'}
        mana_cost = word_to_num.get(mana_word, mana_word)
        
        return f"cmc:{mana_cost} type:{card_type}"
    
    # Handle guild/color + function patterns
    guild_colors = {
        'azorius': 'WU', 'dimir': 'UB', 'rakdos': 'BR', 'gruul': 'RG', 'selesnya': 'GW',
        'orzhov': 'WB', 'izzet': 'UR', 'golgari': 'BG', 'boros': 'RW', 'simic': 'UG',
        'bant': 'GWU', 'esper': 'WUB', 'grixis': 'UBR', 'jund': 'BRG', 'naya': 'RGW',
        'abzan': 'WBG', 'jeskai': 'URW', 'sultai': 'UBG', 'mardu': 'RWB', 'temur': 'GUR'
    }
    
    for guild, colors in guild_colors.items():
        if guild in query:
            if 'counterspell' in query or 'counter' in query:
                return f'coloridentity:{colors} o:"counter target spell"'
            elif 'removal' in query:
                return f'coloridentity:{colors} (o:"destroy" OR o:"damage")'
            elif 'creature' in query:
                return f'coloridentity:{colors} type:creature'
            elif 'instant' in query:
                return f'coloridentity:{colors} type:instant'
            elif 'card draw' in query or 'draw' in query:
                return f'coloridentity:{colors} o:"draw"'
            else:
                return f'coloridentity:{colors}'
    
    # Handle land types
    land_types = {
        'shockland': 'is:shockland',
        'fetchland': 'is:fetchland',
        'triome': 'is:triland',
        'checkland': 'is:checkland',
        'fastland': 'is:fastland',
        'painland': 'is:painland',
        'filterland': 'is:filterland',
        'bounceland': 'is:bounceland',
        'scryland': 'is:scryland',
        'creatureland': 'is:creatureland',
        'manland': 'is:creatureland'
    }
    
    for land_type, scryfall_query in land_types.items():
        if land_type in query:
            # Check if there's a color specification
            for guild, colors in guild_colors.items():
                if guild in query:
                    return f'{scryfall_query} coloridentity:{colors}'
            
            # Check for individual colors
            color_map = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
            for color_name, color_code in color_map.items():
                if color_name in query:
                    return f'{scryfall_query} coloridentity:{color_code}'
            
            return scryfall_query
    
    # Handle commander deck queries
    commanders = {
        'chulane': 'GWU', 'alesha': 'RWB', 'kenrith': 'WUBRG', 'atraxa': 'WUBG',
        'meren': 'BG', 'krenko': 'R', 'sisay': 'WG'
    }
    
    for commander, colors in commanders.items():
        if commander in query:
            if 'counterspell' in query:
                return f'coloridentity:{colors} o:"counter target spell"'
            elif 'removal' in query:
                return f'coloridentity:{colors} (o:"destroy" OR o:"damage")'
            elif 'ramp' in query:
                return f'coloridentity:{colors} (o:"search your library" AND o:"land")'
            else:
                return f'coloridentity:{colors}'
    
    # Handle special card types
    if 'commander' in query:
        color_query = ""
        color_map = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
        for color_name, color_code in color_map.items():
            if color_name in query:
                color_query = f' coloridentity:{color_code}'
                break
        return f'is:commander{color_query}'
    
    if 'vanilla creature' in query:
        return 'is:vanilla type:creature'
    
    if 'french vanilla' in query:
        return 'is:frenchvanilla type:creature'
    
    # Handle basic functional searches
    if 'counterspell' in query or 'counter target spell' in query:
        return 'o:"counter target spell"'
    
    if 'destroy target creature' in query:
        return 'o:"destroy target creature"'
    
    # Fallback: try the original query as-is
    return raw_query

def search_scryfall(filters: dict):
    """Search Scryfall API with built query"""
    query = build_query(filters)
    
    print(f"Scryfall query: {query}")  # Debug output
    
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
            cards = data.get("data", [])
            print(f"Found {len(cards)} cards")  # Debug output
            return cards
        elif response.status_code == 404:
            # No cards found
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
