#!/usr/bin/env python3
"""
Query Builder - A more robust approach to parsing MTG search queries

This replaces the fragile regex-based approach in nlp.py with a builder pattern
that processes tokens sequentially and applies modifiers intelligently.

⚠️ CRITICAL: Scryfall Color Syntax Rules
- COLOR, CMC, COLORIDENTITY must use = operators, NOT : syntax!
- COLOR=R → exactly RED only (mono-red cards)
- COLOR>=R → has RED in it (red + any other colors)  
- COLOR<=R → red color identity (same as COLORIDENTITY=R)
- CMC=3 → exactly 3 mana cost
- Other fields (o:, type:, name:) still use : syntax

Color Logic:
- Individual colors ("blue", "red") → use 'colors' field → COLOR= in Scryfall
- Guild names ("azorius", "simic") → use 'coloridentity' field → COLOR= in Scryfall (exactly those colors)
- Commander context → use 'coloridentity' field → COLOR<= in Scryfall (color identity constraint)
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class QueryState:
    """Holds the current state of query parsing"""
    filters: Dict[str, Any] = field(default_factory=dict)
    tokens: List[str] = field(default_factory=list)
    consumed_tokens: set = field(default_factory=set)
    debug_info: Dict[str, Any] = field(default_factory=dict)


class QueryBuilder:
    """
    Builder pattern for parsing MTG search queries
    
    Process:
    1. Tokenize input
    2. Extract base filters (colors, types, cmc, etc.)
    3. Apply modifiers (removal, counterspell, etc.)
    4. Handle special cases (commanders, guilds, etc.)
    """
    
    # Color mappings
    COLORS = {
        'white': 'W', 'w': 'W',
        'blue': 'U', 'u': 'U', 
        'black': 'B', 'b': 'B',
        'red': 'R', 'r': 'R',
        'green': 'G', 'g': 'G'
    }
    
    # Guild color identities (use coloridentity: for deck building context)
    GUILD_COLORS = {
        'azorius': 'WU', 'dimir': 'UB', 'rakdos': 'BR', 'gruul': 'RG', 'selesnya': 'GW',
        'orzhov': 'WB', 'izzet': 'UR', 'golgari': 'BG', 'boros': 'RW', 'simic': 'GU'
    }
    
    # Shard and wedge color identities
    SHARD_COLORS = {
        'bant': 'GWU', 'esper': 'WUB', 'grixis': 'UBR', 'jund': 'BRG', 'naya': 'RGW'
    }
    
    WEDGE_COLORS = {
        'abzan': 'WBG', 'jeskai': 'URW', 'sultai': 'BGU', 'mardu': 'RWB', 'temur': 'GUR'
    }
    
    # Famous commanders (fallback if commander DB not loaded)
    COMMANDERS = {
        'chulane': 'GWU', 'alesha': 'RWB', 'kenrith': 'WUBRG', 'atraxa': 'WUBG',
        'korvold': 'BRG', 'muldrotha': 'UBG', 'edgar markov': 'RWB', 
        'the ur-dragon': 'WUBRG', 'meren': 'BG', 'omnath': 'WUBRG',
        'niv-mizzet': 'UR', 'rhys': 'GW'
    }
    
    # Card types
    BASIC_TYPES = {
        'creature', 'instant', 'sorcery', 'artifact', 'enchantment', 'planeswalker', 'land'
    }
    
    COMPOUND_TYPES = {
        'artifact creature': 'type:artifact type:creature',
        'legendary creature': 'type:legendary type:creature',
        'tribal instant': 'type:tribal type:instant',
        'enchantment creature': 'type:enchantment type:creature'
    }
    
    # Special land types
    SPECIAL_LANDS = {
        'fetchland': 'o:"search your library" o:"shuffle" type:land',
        'shockland': 'o:"as ~ enters" o:"2 damage" type:land',
        'triome': 'o:"cycling" o:"enters tapped" type:land',
        'dual land': 'o:"{" o:"}" type:land',
        'basic land': 'type:basic type:land',
        'utility land': 'type:land -type:basic'
    }
    
    # Effect modifiers - these transform what we're looking for
    # ORDER MATTERS: More specific patterns should come first
    EFFECT_MODIFIERS = {
        'pump': {
            'patterns': [r'\+1/\+1', r'\+1_\+1', r'adds.*counter', r'put.*\+1/\+1', r'put a \+1/\+1 counter', r'with \+1/\+1 counter'],
            'oracle_text': 'o:"+1/+1 counter"',
            'transforms': {}
        },
        'counterspell': {
            'patterns': ['counterspell', r'\bcounter\b(?!.*cannot)(?!.*can\'t)(?!.*\+1/\+1)(?!.*counter.*on)'],
            'oracle_text': 'o:"counter target"',
            'transforms': {'type': 'instant'}  # Counterspells are typically instants
        },
        'removal': {
            'patterns': ['removal', 'destroy', 'remove'],
            'oracle_text': '(o:destroy or o:"put into" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent)',
            'transforms': {}  # Can be any type
        },
        'graveyard_hate': {
            'patterns': ['graveyard hate', 'exile graveyard', 'graveyard removal', r'exile.*graveyard', r'graveyard.*exile', r'exile.*all.*graveyard'],
            'oracle_text': '(o:"exile" and (o:graveyard or o:"from graveyard" or o:"all graveyards"))',
            'transforms': {}
        },
        'ramp': {
            'patterns': ['ramp', r'mana acceleration', r'search.*land'],
            'oracle_text': '(o:"search your library" o:land) or (o:"add" o:"mana")',
            'transforms': {}
        },
        'draw': {
            'patterns': ['draw', 'card draw'],
            'oracle_text': 'o:"draw" o:"card"',
            'transforms': {}
        },
        'token': {
            'patterns': ['token', r'create.*creature'],
            'oracle_text': 'o:"create" o:"token"',
            'transforms': {}
        },
        'burn': {
            'patterns': ['burn', 'damage', r'deal.*damage'],
            'oracle_text': 'o:"deal" o:"damage"',
            'transforms': {}
        }
    }
    
    def __init__(self):
        self.state = QueryState()
    
    def parse(self, prompt: str) -> Dict[str, Any]:
        """Main entry point - parse a natural language query into filters"""
        self.state = QueryState()
        self.state.tokens = self._tokenize(prompt.lower())
        self.state.debug_info['original_prompt'] = prompt
        self.state.debug_info['tokens'] = self.state.tokens.copy()
        
        print(f"🔧 QueryBuilder parsing: '{prompt}'")
        print(f"🔧 Tokens: {self.state.tokens}")
        
        # Step 1: Extract base filters
        self._extract_mana_cost()
        self._extract_colors()
        self._extract_types()
        self._extract_commanders()
        
        # Step 2: Apply effect modifiers
        self._apply_modifiers()
        
        # Step 3: Handle special cases
        self._handle_special_lands()
        
        print(f"🔧 Final filters: {self.state.filters}")
        return self.state.filters
    
    def _tokenize(self, prompt: str) -> List[str]:
        """Tokenize the prompt, preserving important phrases"""
        # First, protect important multi-word phrases
        protected_phrases = [
            'artifact creature', 'legendary creature', 'tribal instant',
            'enchantment creature', 'card draw', 'mana acceleration',
            '+1/+1 counter', '+1/+1 counters', 'dual land', 'basic land', 'utility land'
        ]
        
        # Replace spaces in protected phrases with underscores temporarily
        working_prompt = prompt
        phrase_map = {}
        for phrase in protected_phrases:
            if phrase in working_prompt:
                placeholder = phrase.replace(' ', '_').replace('/', '_')
                phrase_map[placeholder] = phrase
                working_prompt = working_prompt.replace(phrase, placeholder)
        
        # Tokenize
        tokens = working_prompt.split()
        
        # Restore protected phrases
        for i, token in enumerate(tokens):
            if token in phrase_map:
                tokens[i] = phrase_map[token]
        
        return tokens
    
    def _extract_mana_cost(self):
        """Extract mana cost information with comparison operators"""
        for i, token in enumerate(self.state.tokens):
            if i in self.state.consumed_tokens:
                continue
                
            # Look for patterns like "3+ mana", "5+ cost"
            if token.endswith('+') and token[:-1].isdigit():
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                if next_token in ['mana', 'cost', 'cmc']:
                    value = int(token[:-1])
                    self.state.filters['cmc_gte'] = value
                    self.state.consumed_tokens.add(i)
                    self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found CMC >=: {value}")
                    break
                    
            # Look for patterns like "1 mana", "2 cost", "3 cmc"
            elif token.isdigit():
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                
                # Check for "X or less/fewer mana" pattern
                if (i + 3 < len(self.state.tokens) and 
                    self.state.tokens[i + 1] == 'or' and 
                    self.state.tokens[i + 2] in ['less', 'fewer'] and
                    self.state.tokens[i + 3] in ['mana', 'cost', 'cmc']):
                    value = int(token)
                    self.state.filters['cmc_lte'] = value
                    self.state.consumed_tokens.update([i, i + 1, i + 2, i + 3])
                    print(f"🔧 Found CMC <=: {value}")
                    break
                    
                # Check for "X or more mana" pattern
                elif (i + 3 < len(self.state.tokens) and 
                      self.state.tokens[i + 1] == 'or' and 
                      self.state.tokens[i + 2] == 'more' and
                      self.state.tokens[i + 3] in ['mana', 'cost', 'cmc']):
                    value = int(token)
                    self.state.filters['cmc_gte'] = value
                    self.state.consumed_tokens.update([i, i + 1, i + 2, i + 3])
                    print(f"🔧 Found CMC >=: {value}")
                    break
                    
                # Simple "X mana" pattern
                elif next_token in ['mana', 'cost', 'cmc']:
                    self.state.filters['cmc'] = int(token)
                    self.state.consumed_tokens.add(i)
                    self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found CMC: {token}")
                    break
            
            # Handle special cases like "zero mana", "x cost"
            elif token == 'zero':
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                if next_token in ['mana', 'cost', 'cmc']:
                    self.state.filters['cmc'] = 0
                    self.state.consumed_tokens.add(i)
                    self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found CMC: 0")
                    break
            
            elif token == 'x':
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                if next_token in ['cost', 'mana']:
                    # X cost spells - we'll handle this as a special scryfall query
                    self.state.filters['scryfall_query'] = 'mana>=X'
                    self.state.consumed_tokens.add(i)
                    self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found X cost")
                    break
            
            # Handle descriptive CMC terms
            elif token in ['high', 'expensive']:
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                if next_token in ['cmc', 'cost', 'mana'] or 'cmc' in self.state.tokens:
                    self.state.filters['cmc_gte'] = 6  # High CMC typically means 6+
                    self.state.consumed_tokens.add(i)
                    if next_token in ['cmc', 'cost', 'mana']:
                        self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found high CMC: >=6")
                    break
                    
            elif token in ['low', 'cheap']:
                next_token = self.state.tokens[i + 1] if i + 1 < len(self.state.tokens) else None
                if next_token in ['cmc', 'cost', 'mana'] or 'cmc' in self.state.tokens:
                    self.state.filters['cmc_lte'] = 2  # Low CMC typically means 2 or less
                    self.state.consumed_tokens.add(i)
                    if next_token in ['cmc', 'cost', 'mana']:
                        self.state.consumed_tokens.add(i + 1)
                    print(f"🔧 Found low CMC: <=2")
                    break
    
    def _extract_colors(self):
        """Extract color information - distinguish between colors and color identity"""
        color_identity = None
        is_commander_context = False
        
        # First, check for actual commander context keywords
        prompt_lower = ' '.join(self.state.tokens)
        commander_keywords = [
            'for my', 'for', 'deck', 'commander', 'legal in', 'in my', 
            'edh', 'commander deck', 'my deck'
        ]
        
        for keyword in commander_keywords:
            if keyword in prompt_lower:
                is_commander_context = True
                print(f"🔧 Found commander context keyword: '{keyword}'")
                break
        
        # Check for guild names (always exact match unless commander context detected above)
        for token in self.state.tokens:
            if token in self.GUILD_COLORS:
                color_identity = self.GUILD_COLORS[token]
                print(f"🔧 Found guild: {token} -> {color_identity} ({'commander context' if is_commander_context else 'exact match'})")
                break
        
        # Check for shard/wedge names (always exact match unless commander context detected above)
        if not color_identity:
            for token in self.state.tokens:
                if token in self.SHARD_COLORS:
                    color_identity = self.SHARD_COLORS[token]
                    print(f"🔧 Found shard: {token} -> {color_identity} ({'commander context' if is_commander_context else 'exact match'})")
                    break
                elif token in self.WEDGE_COLORS:
                    color_identity = self.WEDGE_COLORS[token]
                    print(f"🔧 Found wedge: {token} -> {color_identity} ({'commander context' if is_commander_context else 'exact match'})")
                    break
        
        # Check for individual colors (always exact match, never commander context)
        if not color_identity:
            for token in self.state.tokens:
                if token in self.COLORS:
                    color_identity = self.COLORS[token]
                    is_commander_context = False  # Individual colors are never commander context
                    print(f"🔧 Found color: {token} -> {color_identity} (exact match)")
                    break
        
        # Store the appropriate field
        if color_identity:
            if is_commander_context:
                self.state.filters['coloridentity'] = color_identity
                self.state.filters['is_commander_context'] = True
            else:
                self.state.filters['coloridentity'] = color_identity
                self.state.filters['is_commander_context'] = False
    
    def _extract_types(self):
        """Extract card type information"""
        # Check for compound types first
        prompt = ' '.join(self.state.tokens)
        for compound_type, scryfall_query in self.COMPOUND_TYPES.items():
            if compound_type in prompt:
                self.state.filters['scryfall_query'] = scryfall_query
                print(f"🔧 Found compound type: {compound_type}")
                return
        
        # Check for basic types (handle plurals)
        for token in self.state.tokens:
            # Handle plurals by removing 's' if present
            singular_token = token.rstrip('s') if token.endswith('s') and len(token) > 1 else token
            
            if token in self.BASIC_TYPES:
                self.state.filters['type'] = token
                print(f"🔧 Found type: {token}")
                break
            elif singular_token in self.BASIC_TYPES:
                self.state.filters['type'] = singular_token
                print(f"🔧 Found type: {singular_token} (from plural {token})")
                break
    
    def _extract_commanders(self):
        """Extract commander information"""
        prompt = ' '.join(self.state.tokens)
        
        # Look for commander patterns
        commander_patterns = [
            r'for my (\w+(?:[\s\-]+\w+)*) deck',
            r'for (\w+(?:[\s\-]+\w+)*)',
            r'(\w+(?:[\s\-]+\w+)*) commander'
        ]
        
        for pattern in commander_patterns:
            matches = re.findall(pattern, prompt)
            for match in matches:
                commander_name = match.strip()
                
                # Try to find in commander database first
                try:
                    from app.commanders import commander_db
                    if commander_db.loaded:
                        commander_colors = commander_db.get_commander_colors(commander_name)
                        if commander_colors:
                            self.state.filters['coloridentity'] = commander_colors
                            print(f"🔧 Found commander (DB): {commander_name} -> {commander_colors}")
                            return
                except ImportError:
                    pass
                
                # Fallback to hardcoded commanders
                if commander_name in self.COMMANDERS:
                    self.state.filters['coloridentity'] = self.COMMANDERS[commander_name]
                    self.state.filters['is_commander_context'] = True  # Commander detection always means commander context
                    print(f"🔧 Found commander (fallback): {commander_name} -> {self.COMMANDERS[commander_name]} (commander context)")
                    return
    
    def _apply_modifiers(self):
        """Apply effect modifiers that transform the query"""
        prompt = ' '.join(self.state.tokens)
        
        for effect_name, effect_config in self.EFFECT_MODIFIERS.items():
            for pattern in effect_config['patterns']:
                if re.search(pattern, prompt):
                    print(f"🔧 Found modifier: {effect_name}")
                    
                    # Apply transforms
                    for key, value in effect_config['transforms'].items():
                        self.state.filters[key] = value
                    
                    # Handle the effect based on existing filters
                    self._transform_for_effect(effect_name, effect_config)
                    return  # Only apply one modifier for now
    
    def _transform_for_effect(self, effect_name: str, effect_config: Dict):
        """Transform existing filters based on the effect modifier"""
        oracle_text = effect_config['oracle_text']
        
        # If we have a type filter, determine if it's a spell type or target type
        if 'type' in self.state.filters:
            type_value = self.state.filters['type']
            
            # Pure spell types: these describe what the card IS (keep as type filter)
            pure_spell_types = {'instant', 'sorcery'}
            # Pure target types: these describe what the spell AFFECTS (convert to oracle text)
            pure_target_types = {'creature', 'planeswalker'}
            # Ambiguous types: could be either spell type or target type
            ambiguous_types = {'artifact', 'enchantment'}
            # Permanent types: when targeted, include o:permanent clause
            permanent_types = {'artifact', 'creature', 'enchantment', 'planeswalker'}
            
            if effect_name == 'removal':
                if type_value in pure_spell_types:
                    # "instant removal" -> removal spells that are instants
                    self.state.filters['scryfall_query'] = oracle_text
                    # Keep the type filter - we want instant removal spells
                    print(f"🔧 Transformed to {effect_name} spells of type {type_value}")
                elif type_value in pure_target_types:
                    # "creature removal" -> spells that remove creatures
                    self.state.filters['scryfall_query'] = f"{oracle_text} and (o:{type_value} or o:permanent)"
                    del self.state.filters['type']  # We're not looking for creatures, but spells that affect creatures
                    print(f"🔧 Transformed to {effect_name} targeting {type_value} (including permanents)")
                elif type_value in ambiguous_types:
                    # For ambiguous types like "artifact", default to target for removal
                    # "artifact removal" -> spells that remove artifacts
                    self.state.filters['scryfall_query'] = f"{oracle_text} and (o:{type_value} or o:permanent)"
                    del self.state.filters['type']
                    print(f"🔧 Transformed to {effect_name} targeting {type_value} (including permanents)")
                else:
                    # Other types (like land, instant, sorcery when used as targets) - no permanent clause
                    self.state.filters['scryfall_query'] = f"{oracle_text} and o:{type_value}"
                    del self.state.filters['type']
                    print(f"🔧 Transformed to {effect_name} targeting {type_value}")
            
            elif effect_name == 'counterspell':
                # Counterspells are always instants, regardless of what they counter
                if type_value in pure_spell_types:
                    # "instant counterspell" -> counterspells that are instants (redundant but valid)
                    self.state.filters['scryfall_query'] = oracle_text
                    self.state.filters['type'] = 'instant'  # Counterspells are instants
                else:
                    # "creature counterspell" -> counterspells that can counter creatures
                    self.state.filters['scryfall_query'] = oracle_text
                    self.state.filters['type'] = 'instant'  # Override type
                print(f"🔧 Transformed to {effect_name}")
            
            elif effect_name == 'pump':
                # "creature with +1/+1 counters" -> creatures that have/get +1/+1 counters
                self.state.filters['scryfall_query'] = f"type:{type_value} {oracle_text}"
                del self.state.filters['type']  # Replace with scryfall_query
                print(f"🔧 Transformed to {type_value} with {effect_name}")
        
        else:
            # No specific type, just add the effect
            self.state.filters['scryfall_query'] = oracle_text
            print(f"🔧 Added effect: {effect_name}")
    
    def _handle_special_lands(self):
        """Handle special land types"""
        prompt = ' '.join(self.state.tokens)
        
        for land_type, scryfall_query in self.SPECIAL_LANDS.items():
            if land_type in prompt:
                self.state.filters['scryfall_query'] = scryfall_query
                print(f"🔧 Found special land: {land_type}")
                break


# Compatibility function to match nlp.py interface
def extract_filters(prompt: str) -> Dict[str, Any]:
    """Extract filters from natural language prompt using QueryBuilder"""
    builder = QueryBuilder()
    return builder.parse(prompt)


if __name__ == "__main__":
    # Quick test
    test_queries = [
        "1 mana counterspell",
        "blue artifact removal", 
        "removal for Atraxa",
        "fetchland",
        "azorius counterspell"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Testing: {query}")
        result = extract_filters(query)
        print(f"Result: {result}")
