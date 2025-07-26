import requests
import urllib.parse
import time
import re

def build_query(filters: dict) -> str:
    """
    Build Scryfall query from extracted filters
    
    ⚠️ CRITICAL: Scryfall Color Syntax Rules
    - COLOR, CMC, COLORIDENTITY must use = operators, NOT : syntax!
    - COLOR=R → exactly RED only (mono-red cards)
    - COLOR>=R → has RED in it (red + any other colors)  
    - COLOR<=R → red color identity (same as COLORIDENTITY=R)
    - CMC=3 → exactly 3 mana cost
    - Other fields (o:, type:, name:) still use : syntax
    """
    
    # Always include game:paper filter for physical cards only
    base_parts = ["game:paper"]
    
    # Build query from structured filters
    parts = base_parts.copy()
    
    # If we have a direct scryfall query, use it as base but still add other filters
    scryfall_query = ""
    if "scryfall_query" in filters:
        scryfall_query = filters['scryfall_query']
        parts.append(f"({scryfall_query})")
    
    # Mana cost - MUST use = syntax, not : syntax
    if "cmc" in filters:
        parts.append(f"CMC={filters['cmc']}")  # Fixed: was cmc=, now CMC=
    elif "cmc_gte" in filters:
        parts.append(f"CMC>={filters['cmc_gte']}")  # Fixed: was cmc>=, now CMC>=
    elif "cmc_lte" in filters:
        parts.append(f"CMC<={filters['cmc_lte']}")  # Fixed: was cmc<=, now CMC<=
    
    # Card type - uses : syntax (this is correct)
    if "type" in filters:
        type_value = filters['type']
        # If multiple types, wrap in quotes for Scryfall
        if ' ' in type_value:
            parts.append(f'type:"{type_value}"')
        else:
            parts.append(f"type:{type_value}")
    
    # Colors (actual card colors) - MUST use COLOR= syntax, not color:
    if "colors" in filters and f"COLOR={filters['colors']}" not in scryfall_query:
        parts.append(f"COLOR={filters['colors']}")  # Fixed: was color:, now COLOR=
    
    # Color identity - distinguish between guild names (exact) and commander context (identity)
    if "coloridentity" in filters and f"COLOR={filters['coloridentity']}" not in scryfall_query and f"COLOR<={filters['coloridentity']}" not in scryfall_query:
        # For guild names like "azorius" (WU), we want exactly those colors: COLOR=WU
        # For commander context like "removal for Atraxa", we want color identity: COLOR<=WUBG
        # Default to exact match for guild names, query_builder should specify if it's commander context
        if filters.get('is_commander_context', False):
            parts.append(f"COLOR<={filters['coloridentity']}")  # Commander context: color identity constraint
        else:
            parts.append(f"COLOR={filters['coloridentity']}")   # Guild names: exactly those colors
    
    # Color identity exact (requires exact match) - DEPRECATED, use coloridentity instead
    if "coloridentity_exact" in filters:
        parts.append(f"COLOR={filters['coloridentity_exact']}")  # Fixed: was color=, now COLOR=
    
    # Format
    if "format" in filters:
        parts.append(f"format:{filters['format']}")
    
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
    
    # If we have a raw query and no scryfall_query, try to parse it better
    if "raw_query" in filters and "scryfall_query" not in filters:
        raw_parsed = parse_raw_query(filters["raw_query"])
        parts.append(f"({raw_parsed})")
    
    # If no additional parts, return just the base filter
    if len(parts) == 1:  # Only has game:paper
        return "game:paper type:creature"  # Default fallback with game:paper
    
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
    # Colors in WUBRG order (Magic's canonical color order)
    guild_colors = {
        'azorius': 'WU', 'dimir': 'UB', 'rakdos': 'BR', 'gruul': 'RG', 'selesnya': 'GW',
        'orzhov': 'WB', 'izzet': 'UR', 'golgari': 'BG', 'boros': 'RW', 'simic': 'GU',
        'bant': 'GWU', 'esper': 'WUB', 'grixis': 'UBR', 'jund': 'BRG', 'naya': 'RGW',
        'abzan': 'WBG', 'jeskai': 'URW', 'sultai': 'BUG', 'mardu': 'RWB', 'temur': 'GUR'
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

def search_scryfall(filters: dict, page: int = 1):
    """Search Scryfall API with built query, getting specific page"""
    query = build_query(filters)
    
    print(f"Scryfall query: {query}")  # Debug output
    
    # URL encode the query and add page parameter
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.scryfall.com/cards/search?q={encoded_query}&page={page}"
    
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
            total_cards = data.get("total_cards", len(cards))  # Use Scryfall's total count
            
            print(f"Found {total_cards} total cards (showing page {page} with {len(cards)} cards)")
            return {"cards": cards, "query": query, "total_cards": total_cards}
                    
        elif response.status_code == 404:
            # No cards found
            print(f"No results for query: {query}")
            return {"cards": [], "query": query, "total_cards": 0}
        else:
            print(f"Scryfall API error: {response.status_code} - {response.text}")
            return {"cards": [], "query": query, "total_cards": 0}
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {"cards": [], "query": query, "total_cards": 0}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"cards": [], "query": query, "total_cards": 0}
