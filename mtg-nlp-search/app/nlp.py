import json
import re

# Magic: The Gathering vocabulary mappings
GUILD_COLORS = {
    'azorius': 'WU', 'dimir': 'UB', 'rakdos': 'BR', 'gruul': 'RG', 'selesnya': 'GW',
    'orzhov': 'WB', 'izzet': 'UR', 'golgari': 'BG', 'boros': 'RW', 'simic': 'UG'
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
    
    # Extract card types
    card_types = ['instant', 'sorcery', 'creature', 'artifact', 'enchantment', 'planeswalker', 'land']
    for card_type in card_types:
        if card_type in prompt_lower:
            filters['type'] = card_type
            break
    
    # Handle special card type vernacular
    for vernacular, scryfall_query in CARD_TYPES.items():
        if vernacular in prompt_lower:
            return {'scryfall_query': scryfall_query}
    
    # Handle land vernacular
    for land_type, scryfall_query in LAND_TYPES.items():
        if land_type in prompt_lower:
            # Check for color combinations with land types
            color_identity = extract_color_identity(prompt_lower)
            if color_identity:
                return {'scryfall_query': f'{scryfall_query} coloridentity:{color_identity}'}
            return {'scryfall_query': scryfall_query}
    
    # Extract color identity
    color_identity = extract_color_identity(prompt_lower)
    if color_identity:
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

def extract_color_identity(prompt_lower: str) -> str:
    """Extract color identity from guild names, shard names, commanders, etc."""
    
    # Check guild names
    for guild, colors in GUILD_COLORS.items():
        if guild in prompt_lower:
            return colors
    
    # Check shard names  
    for shard, colors in SHARD_COLORS.items():
        if shard in prompt_lower:
            return colors
    
    # Check wedge names
    for wedge, colors in WEDGE_COLORS.items():
        if wedge in prompt_lower:
            return colors
    
    # Check commander names
    for commander, colors in COMMANDERS.items():
        if commander in prompt_lower:
            return colors
    
    # Check individual colors
    color_map = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
    found_colors = []
    for color_name, color_code in color_map.items():
        if color_name in prompt_lower:
            found_colors.append(color_code)
    
    if found_colors:
        return ''.join(sorted(found_colors))
    
    return None

def extract_filters(prompt: str) -> dict:
    """Main filter extraction function with OpenAI + fallback"""
    
    # First try the fallback parser (it's actually more reliable for Magic terms)
    fallback_filters = extract_filters_fallback(prompt)
    
    # If we got a direct scryfall query, use it
    if 'scryfall_query' in fallback_filters:
        return fallback_filters
    
    # Return fallback results
    return fallback_filters if fallback_filters else {"raw_query": prompt}
