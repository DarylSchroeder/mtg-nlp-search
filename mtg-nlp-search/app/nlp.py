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
    'manland': 'is:creatureland',
    'dual land': 'type:land (o:{W} and o:{U}) or (o:{W} and o:{B}) or (o:{W} and o:{R}) or (o:{W} and o:{G}) or (o:{U} and o:{B}) or (o:{U} and o:{R}) or (o:{U} and o:{G}) or (o:{B} and o:{R}) or (o:{B} and o:{G}) or (o:{R} and o:{G})'
}

CARD_TYPES = {
    'commander': 'is:commander',
    'vanilla creature': 'is:vanilla type:creature',
    'french vanilla creature': 'is:frenchvanilla type:creature',
    'double-faced card': 'is:dfc',
    'modal double-faced card': 'is:mdfc',
    'split card': 'is:split',
    'transform card': 'is:transform',
    'spell': 'is:spell',
    'permanent': 'is:permanent'
}

# Famous commanders and their color identities
COMMANDERS = {
    'chulane': 'GWU',
    'alesha': 'RWB', 
    'kenrith': 'WUBRG',
    'atraxa': 'WUBG',
    'korvold': 'BRG',  # Added missing commander
    'muldrotha': 'UBG',
    'edgar markov': 'RWB',
    'the ur-dragon': 'WUBRG',
    'meren': 'BG',
    'krenko': 'R',
    'sisay': 'WG',
    'golos': 'WUBRG',
    'jodah': 'WUBRG',
    'sliver overlord': 'WUBRG'
}

def extract_filters_fallback(prompt: str) -> dict:
    """Fallback parser when OpenAI fails or isn't available"""
    prompt_lower = prompt.lower()
    filters = {}
    
    # Extract mana cost patterns
    # Handle range patterns first (6+, 2 or less, etc.)
    range_patterns = [
        (r'(\d+)\+\s+mana', '>='),  # "6+ mana"
        (r'(\d+)\s*\+\s*mana', '>='),  # "6 + mana"
        (r'(\d+)\s*or\s+less', '<='),  # "2 or less"
        (r'costs?\s+(\d+)\s+or\s+less', '<='),  # "costs 2 or less"
        (r'(\d+)\s+or\s+fewer', '<='),  # "2 or fewer"
    ]
    
    cmc_operator = None
    cmc_value = None
    
    for pattern, operator in range_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            cmc_operator = operator
            cmc_value = int(match.group(1))
            break
    
    if cmc_operator and cmc_value is not None:
        # Store both the numeric value and build scryfall query with operator
        filters['cmc'] = cmc_value
        if 'scryfall_query' not in filters:
            filters['scryfall_query'] = f'cmc{cmc_operator}{cmc_value}'
        else:
            filters['scryfall_query'] += f' cmc{cmc_operator}{cmc_value}'
    else:
        # Handle exact mana costs if no range found
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
    
    # Handle X cost spells
    if re.search(r'\bx\s+cost', prompt_lower) or re.search(r'\bx\s+mana', prompt_lower):
        cmc_value = 1  # X costs are typically 1 or more
        filters['cmc'] = cmc_value
        if 'scryfall_query' not in filters:
            filters['scryfall_query'] = f'cmc>={cmc_value}'
        else:
            filters['scryfall_query'] += f' cmc>={cmc_value}'
    
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
    
    # If multiple types found, create separate type: queries for Scryfall
    if found_types:
        if len(found_types) > 1:
            # Sort types to match Scryfall's expected order (artifact before creature)
            type_order = {'artifact': 0, 'creature': 1, 'enchantment': 2, 'instant': 3, 'sorcery': 4, 'planeswalker': 5, 'land': 6}
            found_types.sort(key=lambda x: type_order.get(x, 99))
            
            # For multiple types, create individual type: queries
            type_queries = [f'type:{t}' for t in found_types]
            type_query = ' '.join(type_queries)
            
            if 'scryfall_query' not in filters:
                filters['scryfall_query'] = type_query
            else:
                filters['scryfall_query'] += f' {type_query}'
            
            # Also store the combined type for backward compatibility
            filters['type'] = ' '.join(found_types)
        else:
            filters['type'] = found_types[0]
    
    # Handle special card type vernacular
    spell_or_permanent_query = None
    for vernacular, scryfall_query in CARD_TYPES.items():
        if vernacular in prompt_lower:
            # For commander queries, check for color combinations
            if vernacular == 'commander':
                color_result = extract_color_identity(prompt_lower)
                if color_result[0]:  # If color_identity is not None
                    color_identity, is_commander_context = color_result[0], color_result[1]
                    # Commander queries always use coloridentity
                    return {'scryfall_query': f'{scryfall_query} coloridentity:{color_identity}'}
                return {'scryfall_query': scryfall_query}
            # For spell and permanent, store the query but continue processing for effects
            elif vernacular in ['spell', 'permanent']:
                spell_or_permanent_query = scryfall_query
            else:
                return {'scryfall_query': scryfall_query}
    
    # Handle land vernacular
    for land_type, scryfall_query in LAND_TYPES.items():
        if land_type in prompt_lower:
            # Check for color combinations with land types
            color_result = extract_color_identity(prompt_lower)
            
            # Always set type:land for land queries
            filters['type'] = 'land'
            
            if color_result[0]:  # If color_identity is not None
                color_identity, is_commander_context = color_result[0], color_result[1]
                # Land types always use coloridentity for deck building context
                return {'type': 'land', 'coloridentity': color_identity, 'scryfall_query': f'{scryfall_query} coloridentity:{color_identity}'}
            return {'type': 'land', 'scryfall_query': scryfall_query}
    
    # Extract color identity
    print(f"🔍 DEBUG: About to call extract_color_identity with: '{prompt_lower}'")
    color_result = extract_color_identity(prompt_lower)
    color_identity, is_commander_context, color_debug = color_result[0], color_result[1], color_result[2]
    print(f"🔍 DEBUG: extract_color_identity returned: {color_result}")
    
    if color_identity:
        if is_commander_context:
            # Commander context uses coloridentity
            filters['coloridentity'] = color_identity
            print(f"🔍 DEBUG: Added coloridentity filter: {color_identity}")
        else:
            # Everything else uses color
            filters['colors'] = color_identity
            print(f"🔍 DEBUG: Added colors filter: {color_identity}")
    else:
        print(f"🔍 DEBUG: No color identity found, checking individual colors")
        # Check for individual colors if no guild/commander context found
        individual_colors = []
        import re
        for color_name, color_code in COLOR_MAP.items():
            # Use word boundaries to prevent substring matches
            pattern = r'\b' + re.escape(color_name.lower()) + r'\b'
            if re.search(pattern, prompt_lower):
                print(f"🔍 DEBUG: Individual color found - '{color_name}' -> {color_code}")
                individual_colors.append(color_code)
        
        if individual_colors:
            color_string = ''.join(sorted(individual_colors))
            filters["colors"] = color_string
            print(f"🔍 DEBUG: Added individual colors filter: {color_string}")
        else:
            print(f"🔍 DEBUG: No colors found at all")
    
    # Add debug info to filters
    filters['_debug_color'] = color_debug
    
    # Extract format information
    format_patterns = {
        'standard': [r'\bstandard\b', r'format:standard'],
        'commander': [r'\bcommander\b', r'\bedh\b', r'format:commander'],
        'modern': [r'\bmodern\b', r'format:modern'],
        'pioneer': [r'\bpioneer\b', r'format:pioneer'],
        'legacy': [r'\blegacy\b', r'format:legacy'],
        'pauper': [r'\bpauper\b', r'format:pauper']
    }
    
    for format_name, patterns in format_patterns.items():
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                filters['format'] = format_name
                break
        if 'format' in filters:
            break
    
    # Extract common effects
    effects = []
    effect_patterns = {
        'counter': ['counterspell', r'\bcounters?\b(?!.*cannot be countered)(?!.*can\'t be countered)'],
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
                elif pattern.startswith(r'\bcounters?\b'):
                    # Check if "counter" or "counters" appears but NOT in "cannot be countered" context
                    if re.search(r'\bcounters?\b', prompt_lower):
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
    
    # Handle spell/permanent queries with effects
    if spell_or_permanent_query and effects:
        # Combine spell/permanent query with effect queries
        effect_queries = [f'effect[{effect}]' for effect in effects]
        combined_query = f'{spell_or_permanent_query} {" ".join(effect_queries)}'
        filters['scryfall_query'] = combined_query
    elif spell_or_permanent_query:
        # Just spell/permanent without effects
        filters['scryfall_query'] = spell_or_permanent_query
    
    return filters

def extract_color_identity(prompt_lower: str) -> tuple:
    """Extract color information from guild names, shard names, commanders, etc.
    Returns (color_identity, is_commander_context, debug_info) where:
    - color_identity is the color string (e.g., 'BR', 'GWU')
    - is_commander_context is True when we should use 'coloridentity:' instead of 'color:'
    - debug_info contains matching details for debugging
    """
    
    debug_info = {
        "input": prompt_lower,
        "guild_matches": [],
        "shard_matches": [],
        "wedge_matches": [],
        "commander_matches": [],
        "fallback_commander_matches": []
    }
    
    print(f"🎨 DEBUG: extract_color_identity called with: '{prompt_lower}'")
    color_identity = None
    is_commander_context = False
    
    # Check guild names - use coloridentity for deck building context
    import re
    for guild, colors in GUILD_COLORS.items():
        # Use word boundaries to prevent substring matches
        pattern = r'\b' + re.escape(guild.lower()) + r'\b'
        if re.search(pattern, prompt_lower):
            print(f"🏛️ DEBUG: Guild match found - '{guild}' -> {colors}")
            debug_info["guild_matches"].append({"name": guild, "colors": colors})
            color_identity = colors
            is_commander_context = True  # Guild names imply deck building context
            break
    
    # Check shard names - use coloridentity for deck building context
    if not color_identity:
        for shard, colors in SHARD_COLORS.items():
            # Use word boundaries to prevent substring matches
            pattern = r'\b' + re.escape(shard.lower()) + r'\b'
            if re.search(pattern, prompt_lower):
                print(f"🔺 DEBUG: Shard match found - '{shard}' -> {colors}")
                debug_info["shard_matches"].append({"name": shard, "colors": colors})
                color_identity = colors
                is_commander_context = True  # Shard names imply deck building context
                break
    
    # Check wedge names - use coloridentity for deck building context
    if not color_identity:
        for wedge, colors in WEDGE_COLORS.items():
            # Use word boundaries to prevent substring matches
            pattern = r'\b' + re.escape(wedge.lower()) + r'\b'
            if re.search(pattern, prompt_lower):
                print(f"🔶 DEBUG: Wedge match found - '{wedge}' -> {colors}")
                debug_info["wedge_matches"].append({"name": wedge, "colors": colors})
                color_identity = colors
                is_commander_context = True  # Wedge names imply deck building context
                break
    
    # Check commander names using dynamic database - use coloridentity
    if not color_identity:
        from app.commanders import commander_db
        
        if commander_db.loaded:
            # Try to extract commander name from common patterns
            import re
            commander_patterns = [
                r'for my (\w+(?:\s+\w+)*) deck',
                r'in (\w+(?:\s+\w+)*) colors',
                r'(\w+(?:\s+\w+)*) commander',
                r'for (\w+(?:\s+\w+)*)',
            ]
            
            for pattern in commander_patterns:
                matches = re.findall(pattern, prompt_lower)
                for match in matches:
                    commander_colors = commander_db.get_commander_colors(match.strip())
                    if commander_colors:
                        color_identity = commander_colors
                        is_commander_context = True
                        break
                if color_identity:
                    break
            
            # Also check direct commander name mentions
            if not color_identity:
                import re
                for commander_name in commander_db.commanders.keys():
                    # Use word boundaries to prevent substring matches
                    pattern = r'\b' + re.escape(commander_name.lower()) + r'\b'
                    if re.search(pattern, prompt_lower):
                        print(f"👑 DEBUG: Commander match found - '{commander_name}' -> {commander_db.commanders[commander_name]}")
                        debug_info["commander_matches"].append({
                            "name": commander_name, 
                            "colors": commander_db.commanders[commander_name]
                        })
                        color_identity = commander_db.commanders[commander_name]
                        is_commander_context = True
                        break
        else:
            # Fallback to hardcoded commanders if database not loaded
            import re
            for commander, colors in COMMANDERS.items():
                # Use word boundaries to prevent substring matches
                pattern = r'\b' + re.escape(commander.lower()) + r'\b'
                if re.search(pattern, prompt_lower):
                    print(f"👑 DEBUG: Fallback commander match found - '{commander}' -> {colors}")
                    debug_info["fallback_commander_matches"].append({
                        "name": commander, 
                        "colors": colors
                    })
                    color_identity = colors
                    is_commander_context = True
                    break
    
    # Check individual colors - always use color
    if not color_identity:
        color_map = {'white': 'W', 'blue': 'U', 'black': 'B', 'red': 'R', 'green': 'G'}
        found_colors = []
        for color_name, color_code in color_map.items():
            if color_name in prompt_lower:
                found_colors.append(color_code)
        
        if found_colors:
            color_identity = ''.join(sorted(found_colors))
    
    print(f"🎨 DEBUG: extract_color_identity result - color_identity: '{color_identity}', is_commander_context: {is_commander_context}")
    return color_identity, is_commander_context, debug_info

def extract_filters(prompt: str) -> dict:
    """Main filter extraction function with OpenAI + fallback"""
    
    # First try the fallback parser (it's actually more reliable for Magic terms)
    fallback_filters = extract_filters_fallback(prompt)
    
    # If we got a direct scryfall query, use it
    if 'scryfall_query' in fallback_filters:
        return fallback_filters
    
    # Return fallback results
    return fallback_filters if fallback_filters else {"raw_query": prompt}
