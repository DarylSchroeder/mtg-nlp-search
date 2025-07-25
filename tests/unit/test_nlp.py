#!/usr/bin/env python3
"""
Unit tests for NLP parsing functionality
Consolidated from: test_nlp_parsing.sh, test_color_vs_identity.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../mtg-nlp-search'))

from app.nlp import extract_filters

def test_counter_effect_detection():
    """Test that counter effect detection works correctly (critical bug fix)"""
    
    # These should NOT be detected as counterspells
    negative_cases = [
        "Abrupt Decay",
        "Cannot be countered", 
        "Can't be countered",
        "Cards that cannot be countered"
    ]
    
    for query in negative_cases:
        result = extract_filters(query)
        effects = result.get("effects", [])
        assert "counter" not in effects, f"'{query}' should NOT be counterspell"
        print(f"✅ PASS: '{query}' correctly NOT detected as counterspell")
    
    # These SHOULD be detected as counterspells
    positive_cases = [
        "Counterspell",
        "1 mana counterspell", 
        "Blue counterspell"
    ]
    
    for query in positive_cases:
        result = extract_filters(query)
        effects = result.get("effects", [])
        assert "counter" in effects, f"'{query}' should BE counterspell"
        print(f"✅ PASS: '{query}' correctly detected as counterspell")

def test_mana_cost_extraction():
    """Test mana cost parsing"""
    
    test_cases = [
        ("1 mana spell", 1),
        ("2 mana creature", 2), 
        ("Zero mana spell", 0),
        ("No mana mentioned", None)
    ]
    
    for query, expected_cmc in test_cases:
        result = extract_filters(query)
        actual_cmc = result.get("cmc")
        
        if expected_cmc is None:
            assert actual_cmc is None, f"'{query}' should have no CMC"
        else:
            assert actual_cmc == expected_cmc, f"'{query}' should have CMC {expected_cmc}, got {actual_cmc}"
        
        print(f"✅ PASS: '{query}' -> CMC: {actual_cmc}")

def test_color_vs_identity_logic():
    """Test color vs color identity distinction"""
    
    # Colors and guild names should use 'colors' field
    color_cases = [
        ("1 cmc white artifact", {"cmc": 1, "type": "artifact", "colors": "W"}),
        ("blue creature 3 mana", {"cmc": 3, "type": "creature", "colors": "U"}),
        ("red instant 2 cmc", {"cmc": 2, "type": "instant", "colors": "R"}),
        ("green sorcery", {"type": "sorcery", "colors": "G"}),
        ("black enchantment", {"type": "enchantment", "colors": "B"}),
        ("rakdos removal", {"coloridentity": "BR"}),  # Guild names use coloridentity
        ("selesnya enchantment", {"type": "enchantment", "coloridentity": "GW"}),  # Guild names use coloridentity
        ("azorius counterspell", {"coloridentity": "WU"})  # Guild names use coloridentity
    ]
    
    for query, expected_filters in color_cases:
        result = extract_filters(query)
        
        for key, expected_value in expected_filters.items():
            actual_value = result.get(key)
            assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
        
        # Check if this is a guild name (should use coloridentity) or individual color (should use colors)
        guild_names = ['rakdos', 'selesnya', 'azorius', 'dimir', 'gruul', 'orzhov', 'izzet', 'golgari', 'boros', 'simic']
        is_guild_query = any(guild in query.lower() for guild in guild_names)
        
        if is_guild_query:
            # Guild names should use coloridentity
            assert 'coloridentity' in result, f"'{query}' should have 'coloridentity' field (guild name)"
            assert 'colors' not in result, f"'{query}' should not have 'colors' field (guild name)"
        else:
            # Individual colors should use colors
            assert 'colors' in result, f"'{query}' should have 'colors' field (individual color)"
            assert 'coloridentity' not in result, f"'{query}' should not have 'coloridentity' field (individual color)"
            
        print(f"✅ PASS: '{query}' uses {'coloridentity' if is_guild_query else 'colors'} correctly")
    
    # Commander contexts should use 'coloridentity'
    commander_cases = [
        "counterspell for my Chulane deck",
        "white fetchland for Chulane", 
        "blue shockland for my Chulane deck",
        "Chulane commander"
    ]
    
    for query in commander_cases:
        result = extract_filters(query)
        
        # Check if coloridentity is used either as a field or in scryfall_query
        has_coloridentity_field = "coloridentity" in result
        scryfall_query = result.get("scryfall_query", "")
        has_coloridentity_query = "coloridentity:" in scryfall_query
        
        assert has_coloridentity_field or has_coloridentity_query, f"'{query}' should use coloridentity"
        print(f"✅ PASS: '{query}' uses coloridentity")

def test_special_card_types():
    """Test special card type detection"""
    
    special_cases = [
        ("fetchland", "fetchland"),
        ("shockland", "shockland"),
        ("commander", "commander")
    ]
    
    for query, expected_type in special_cases:
        result = extract_filters(query)
        
        # Check if it's in scryfall_query or special handling
        scryfall_query = result.get("scryfall_query", "")
        special_types = result.get("special_types", [])
        
        found = expected_type in scryfall_query or expected_type in special_types
        assert found, f"'{query}' should detect {expected_type}"
        
        print(f"✅ PASS: '{query}' detected special type")

if __name__ == "__main__":
    print("🧠 Running NLP Unit Tests...")
    print("=" * 50)
    
    try:
        test_counter_effect_detection()
        print()
        test_mana_cost_extraction() 
        print()
        test_color_vs_identity_logic()
        print()
        test_special_card_types()
        
        print("=" * 50)
        print("✅ All NLP unit tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
