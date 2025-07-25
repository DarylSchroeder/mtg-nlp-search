import json
import re

# Magic: The Gathering vocabulary mappings
GUILD_COLORS = {
    'azorius': 'WU', 'dimir': 'UB', 'rakdos': 'BR', 'gruul': 'RG', 'selesnya': 'GW',
    'orzhov': 'WB', 'izzet': 'UR', 'golgari': 'BG', 'boros': 'RW', 'simic': 'GU'
}

SHARD_COLORS = {
    'bant': 'GWU', 'esper': 'WUB', 'grixis': 'UBR', 'jund': 'BRG', 'naya': 'RGW'
}

WEDGE_COLORS = {
    'abzan': 'WBG', 'jeskai': 'URW', 'sultai': 'UBG', 'mardu': 'RWB', 'temur': 'GUR'
}

LAND_TYPES = {
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

CARD_TYPES = {
    'commander': 'is:commander',
    'vanilla creature': 'is:vanilla type:creature',
    'french vanilla creature': 'is:frenchvanilla type:creature',
    'double-faced card': 'is:dfc',
    'modal double-faced card': 'is:mdfc',
    'split card': 'is:split',
    'transform card': 'is:transform'
}

# Famous commanders and their color identities
COMMANDERS = {
    'chulane': 'GWU',
    'alesha': 'RWB', 
    'kenrith': 'WUBRG',
    'atraxa': 'WUBG',
    'meren': 'BG',
    'krenko': 'R',
    'sisay': 'WG'
}

def extract_filters_fallback(prompt: str) -> dict:
    """Fallback parser when OpenAI fails or isn't available"""
    prompt_lower = prompt.lower()
    filters = {}
    
    # Extract mana cost patterns
    mana_patterns = [
        r'(\d+)\s+mana',
        r'cmc\s*:?\s*(\d+)',
        r'(\d+)\s+cmc',  # Added pattern for "1 cmc", "2 cmc", etc.
        r'costs?\s+(\d+)',
        r'(\d+)\s+cost'
    ]
    
    for pattern in mana_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            filters['cmc'] = int(match.group(1))
            break
    
    # Handle zero mana specially
    if 'zero mana' in prompt_lower or '0 mana' in prompt_lower:
        filters['cmc'] = 0
    
    # Extract power/toughness
    pt_match = re.search(r'(\d+)/(\d+)', prompt)
    if pt_match:
        filters['power'] = int(pt_match.group(1))
        filters['toughness'] = int(pt_match.group(2))
    
    # Extract card types - handle multiple types like "artifact creature"
    card_types = ['instant', 'sorcery', 'creature', 'artifact', 'enchantment', 'planeswalker', 'land']
    found_types = []
    for card_type in card_types:
        if card_type in prompt_lower:
            found_types.append(card_type)
    
    # If multiple types found, combine them in the correct order for Scryfall
    if found_types:
        if len(found_types) > 1:
            # Sort types to match Scryfall's expected order (artifact before creature)
            type_order = {'artifact': 0, 'creature': 1, 'enchantment': 2, 'instant': 3, 'sorcery': 4, 'planeswalker': 5, 'land': 6}
            found_types.sort(key=lambda x: type_order.get(x, 99))
            filters['type'] = ' '.join(found_types)
        else:
            filters['type'] = found_types[0]
    
    # Handle special card type vernacular
    for vernacular, scryfall_query in CARD_TYPES.items():
        if vernacular in prompt_lower:
            # For commander queries, check for color combinations
            if vernacular == 'commander':
                color_result = extract_color_identity(prompt_lower)
                if color_result[0]:  # If color_identity is not None
                    color_identity, exact_match = color_result[0], color_result[1]
                    if exact_match:
                        return {'scryfall_query': f'{scryfall_query} coloridentity={color_identity}'}
                    else:
                        return {'scryfall_query': f'{scryfall_query} coloridentity:{color_identity}'}
            return {'scryfall_query': scryfall_query}
    
    # Handle land vernacular
    for land_type, scryfall_query in LAND_TYPES.items():
        if land_type in prompt_lower:
            # Check for color combinations with land types
            color_result = extract_color_identity(prompt_lower)
            if color_result[0]:  # If color_identity is not None
                color_identity, exact_match = color_result[0], color_result[1]
                if exact_match:
                    return {'scryfall_query': f'{scryfall_query} coloridentity={color_identity}'}
                else:
                    return {'scryfall_query': f'{scryfall_query} coloridentity:{color_identity}'}
            return {'scryfall_query': scryfall_query}
    
    # Extract color identity
    color_result = extract_color_identity(prompt_lower)
    if color_result[0]:  # If color_identity is not None
        color_identity, exact_match = color_result[0], color_result[1]
        use_color_not_identity = len(color_result) > 2 and color_result[2]
        
        if use_color_not_identity:
            # Use actual card color instead of color identity
            filters['colors'] = color_identity
        elif exact_match:
            filters['coloridentity_exact'] = color_identity
        else:
            filters['coloridentity'] = color_identity
    
    # Extract common effects
    effects = []
    effect_patterns = {
        'counter': ['counterspell', r'\bcounter\b(?!.*cannot be countered)(?!.*can\'t be countered)'],
        'draw': ['draw', 'card draw'],
        'removal': ['destroy', 'remove', 'removal'],
        'ramp': [r'\bramp\b', r'search.*land(?!.*mana)', 'acceleration', 'mana acceleration'],
        'token': ['token', 'create.*creature'],
        'damage': ['damage', 'deal.*damage'],
        'life': ['life', 'gain.*life'],
        'flying': ['flying'],
        'vigilance': ['vigilance'],
        'trample': ['trample'],
        'haste': ['haste'],
        'defender': ['defender'],
        'flashback': ['flashback'],
        'tap': ['tap', 'untap']
    }
    
    for effect, patterns in effect_patterns.items():
        for pattern in patterns:
            # Special handling for counter effect to avoid "cannot be countered"
            if effect == 'counter':
                if pattern == 'counterspell' and 'counterspell' in prompt_lower:
                    effects.append(effect)
                    break
                elif pattern.startswith(r'\bcounter\b'):
                    # Check if "counter" appears but NOT in "cannot be countered" context
                    if re.search(r'\bcounter\b', prompt_lower):
                        # Exclude if it's in a "cannot be countered" context
                        if not re.search(r'cannot be countered|can\'t be countered|this spell cannot be countered', prompt_lower):
                            effects.append(effect)
                            break
            else:
                if re.search(pattern, prompt_lower):
                    effects.append(effect)
                    break
    
    if effects:
        filters['effects'] = effects
    
    return filters

def extract_color_identity(prompt_lower: str) -> tuple:
    """Extract color identity from guild names, shard names, commanders, etc.
    Returns (color_identity, exact_match, use_color_not_identity) where:
    - exact_match is True for ':only' suffix
    - use_color_not_identity is True when we should use 'color:' instead of 'coloridentity:'
    """
    
    exact_match = False
    color_identity = None
    
    # Check guild names with :only suffix
    for guild, colors in GUILD_COLORS.items():
        if f"{guild}:only" in prompt_lower:
            return colors, True
        elif guild in prompt_lower:
            color_identity = colors
    
    # Check shard names with :only suffix
    for shard, colors in SHARD_COLORS.items():
        if f"{shard}:only" in prompt_lower:
            return colors, True
        elif shard in prompt_lower:
            color_identity = colors
    
    # Check wedge names with :only suffix
    for wedge, colors in WEDGE_COLORS.items():
        if f"{wedge}:only" in prompt_lower:
            return colors, True
        elif wedge in prompt_lower:
            color_identity = colors
    
    # Check commander names with :only suffix
    for commander, colors in COMMANDERS.items():
        if f"{commander}:only" in prompt_lower:
            return colors, True
        elif commander in prompt_lower:
            color_identity = colors
    
    # Check individual colors
    color_map = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
    found_colors = []
    for color_name, color_code in color_map.items():
        if color_name in prompt_lower:
            found_colors.append(color_code)
    
    if found_colors:
        # For artifacts and most card types, use actual color, not color identity
        # Color identity is mainly for Commander deck building
        if any(card_type in prompt_lower for card_type in ['artifact', 'creature', 'instant', 'sorcery', 'enchantment', 'planeswalker']):
            color_identity = ''.join(sorted(found_colors))
            # Use 'colors' field instead of 'coloridentity' for actual card colors
            return color_identity, False, True  # Return (colors, exact_match, use_color_not_identity)
        else:
            color_identity = ''.join(sorted(found_colors))
    
    return color_identity, exact_match, False

def extract_filters(prompt: str) -> dict:
    """Main filter extraction function with OpenAI + fallback"""
    
    # First try the fallback parser (it's actually more reliable for Magic terms)
    fallback_filters = extract_filters_fallback(prompt)
    
    # If we got a direct scryfall query, use it
    if 'scryfall_query' in fallback_filters:
        return fallback_filters
    
    # Return fallback results
    return fallback_filters if fallback_filters else {"raw_query": prompt}
