#!/usr/bin/env python3
"""
Unit tests for NLP parsing functionality
Consolidated from: test_nlp_parsing.sh, test_color_vs_identity.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../mtg-nlp-search'))

from app.query_builder import extract_filters

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
        scryfall_query = result.get("scryfall_query", "")
        assert "counter target" in scryfall_query, f"'{query}' should BE counterspell"
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
    """Test color vs color identity distinction with explicit commander handling"""
    
    # Individual colors and guild names should use 'colors' field
    color_cases = [
        ("1 cmc white artifact", {"cmc": 1, "type": "artifact", "colors": "W"}),
        ("blue creature 3 mana", {"cmc": 3, "type": "creature", "colors": "U"}),
        ("red instant 2 cmc", {"cmc": 2, "type": "instant", "colors": "R"}),
        ("green sorcery", {"type": "sorcery", "colors": "G"}),
        ("black enchantment", {"type": "enchantment", "colors": "B"}),
        ("rakdos removal", {"colors": "BR"}),  # Guild names use colors (exact match)
        ("selesnya enchantment", {"type": "enchantment", "colors": "GW"}),  # Guild names use colors (exact match)
        ("azorius counterspell", {"colors": "WU"})  # Guild names use colors (exact match)
    ]
    
    for query, expected_filters in color_cases:
        result = extract_filters(query)
        
        for key, expected_value in expected_filters.items():
            actual_value = result.get(key)
            assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
        
        # All these should use 'colors' field, NOT 'coloridentity'
        assert 'colors' in result, f"'{query}' should have 'colors' field"
        assert 'coloridentity' not in result, f"'{query}' should NOT have 'coloridentity' field (explicit commander handling)"
            
        print(f"✅ PASS: '{query}' uses colors correctly")
    
    # Commander context phrases should mark context but NOT set coloridentity automatically
    commander_context_cases = [
        ("counterspell for my Chulane deck", {"is_commander_context": True, "type": "instant"}),
        ("removal for Atraxa", {"is_commander_context": True}),
        ("white fetchland for Chulane", {"colors": "W", "is_commander_context": True}),
        ("blue shockland for my deck", {"colors": "U", "is_commander_context": True}),
        ("Chulane commander", {"is_commander_context": True})
    ]
    
    for query, expected_filters in commander_context_cases:
        result = extract_filters(query)
        
        for key, expected_value in expected_filters.items():
            actual_value = result.get(key)
            assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
        
        # Should mark commander context but NOT automatically set coloridentity
        assert result.get('is_commander_context') == True, f"'{query}' should mark commander context"
        assert 'coloridentity' not in result, f"'{query}' should NOT automatically set coloridentity (explicit commander handling)"
        
        print(f"✅ PASS: '{query}' marks commander context without auto-coloridentity")

def test_special_card_types():
    """Test special card type detection"""
    
    special_cases = [
        ("fetchland", "fetchland"),
        ("shockland", "shockland")
        # Note: "commander" is no longer a special card type - it's a context marker
    ]
    
    for query, expected_type in special_cases:
        result = extract_filters(query)
        
        # Check if it's in scryfall_query or special handling
        scryfall_query = result.get("scryfall_query", "")
        special_types = result.get("special_types", [])
        
        # For fetchland and shockland, check for the is: syntax
        if expected_type == "fetchland":
            found = "is:fetchland" in scryfall_query
        elif expected_type == "shockland":
            found = "is:shockland" in scryfall_query
        else:
            found = expected_type in scryfall_query or expected_type in special_types
            
        assert found, f"'{query}' should detect {expected_type}"
        
        print(f"✅ PASS: '{query}' detected special type")
    
    # Test commander context detection separately
    result = extract_filters("commander")
    assert result.get('is_commander_context') == True, "'commander' should mark commander context"
    print("✅ PASS: 'commander' marks commander context")

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
