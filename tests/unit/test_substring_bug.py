#!/usr/bin/env python3
"""
Unit tests for substring matching bug fixes

Tests the specific issue where "artifact" was matching "tifa" commander
and "enchantment" was matching partial commander/guild names.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../mtg-nlp-search'))

from app.nlp import extract_color_identity

def test_artifact_tifa_bug():
    """Test that 'artifact' doesn't match 'tifa' commander"""
    
    # Mock commander database with tifa
    class MockCommanderDB:
        def __init__(self):
            self.loaded = True
            self.commanders = {
                'tifa': 'G',  # This was causing the bug
                'chulane': 'GWU',
                'alesha': 'RWB'
            }
    
    # Temporarily replace the commander_db import
    import app.nlp
    original_commander_db = getattr(app.nlp, 'commander_db', None)
    
    # Mock the commander_db
    app.nlp.commander_db = MockCommanderDB()
    
    try:
        # Test the bug case
        result = extract_color_identity("1 cmc white artifact")
        color_identity, is_commander_context, debug_info = result
        
        print(f"Input: '1 cmc white artifact'")
        print(f"Color identity: {color_identity}")
        print(f"Is commander context: {is_commander_context}")
        print(f"Commander matches: {debug_info['commander_matches']}")
        
        # Should NOT match tifa commander
        assert color_identity is None, f"Expected no color identity, got {color_identity}"
        assert not is_commander_context, f"Expected not commander context, got {is_commander_context}"
        assert len(debug_info['commander_matches']) == 0, f"Expected no commander matches, got {debug_info['commander_matches']}"
        
        print("✅ PASS: 'artifact' does not match 'tifa'")
        
    finally:
        # Restore original commander_db
        if original_commander_db:
            app.nlp.commander_db = original_commander_db

def test_enchantment_substring_bug():
    """Test that 'enchantment' doesn't match partial names"""
    
    # Mock commander database with names that contain 'ench'
    class MockCommanderDB:
        def __init__(self):
            self.loaded = True
            self.commanders = {
                'enchantress': 'GRU',  # Contains 'ench'
                'french_vanilla': 'W',  # Contains 'ench' 
                'chulane': 'GWU'
            }
    
    # Temporarily replace the commander_db import
    import app.nlp
    original_commander_db = getattr(app.nlp, 'commander_db', None)
    
    # Mock the commander_db
    app.nlp.commander_db = MockCommanderDB()
    
    try:
        # Test the bug case
        result = extract_color_identity("enchantment removal")
        color_identity, is_commander_context, debug_info = result
        
        print(f"\nInput: 'enchantment removal'")
        print(f"Color identity: {color_identity}")
        print(f"Is commander context: {is_commander_context}")
        print(f"Commander matches: {debug_info['commander_matches']}")
        
        # Should NOT match enchantress or french_vanilla
        assert color_identity is None, f"Expected no color identity, got {color_identity}"
        assert not is_commander_context, f"Expected not commander context, got {is_commander_context}"
        assert len(debug_info['commander_matches']) == 0, f"Expected no commander matches, got {debug_info['commander_matches']}"
        
        print("✅ PASS: 'enchantment' does not match partial names")
        
    finally:
        # Restore original commander_db
        if original_commander_db:
            app.nlp.commander_db = original_commander_db

def test_legitimate_commander_match():
    """Test that legitimate commander names still work"""
    
    # Mock commander database
    class MockCommanderDB:
        def __init__(self):
            self.loaded = True
            self.commanders = {
                'tifa': 'G',
                'chulane': 'GWU',
                'alesha': 'RWB'
            }
    
    # Temporarily replace the commander_db import
    import app.nlp
    original_commander_db = getattr(app.nlp, 'commander_db', None)
    
    # Mock the commander_db
    app.nlp.commander_db = MockCommanderDB()
    
    try:
        # Test legitimate commander mention
        result = extract_color_identity("counterspell for my chulane deck")
        color_identity, is_commander_context, debug_info = result
        
        print(f"\nInput: 'counterspell for my chulane deck'")
        print(f"Color identity: {color_identity}")
        print(f"Is commander context: {is_commander_context}")
        print(f"Commander matches: {debug_info['commander_matches']}")
        
        # Should match chulane
        assert color_identity == 'GWU', f"Expected 'GWU', got {color_identity}"
        assert is_commander_context == True, f"Expected commander context, got {is_commander_context}"
        
        # Check if match was found in either commander_matches or fallback_commander_matches
        total_matches = len(debug_info['commander_matches']) + len(debug_info['fallback_commander_matches'])
        assert total_matches == 1, f"Expected 1 total commander match, got {debug_info}"
        
        # Check which section found the match
        if debug_info['commander_matches']:
            assert debug_info['commander_matches'][0]['name'] == 'chulane', f"Expected chulane match in commander_matches"
        elif debug_info['fallback_commander_matches']:
            assert debug_info['fallback_commander_matches'][0]['name'] == 'chulane', f"Expected chulane match in fallback_commander_matches"
        
        print("✅ PASS: Legitimate commander names still work")
        
    finally:
        # Restore original commander_db
        if original_commander_db:
            app.nlp.commander_db = original_commander_db

def test_individual_colors_still_work():
    """Test that individual color detection still works"""
    
    # Mock empty commander database
    class MockCommanderDB:
        def __init__(self):
            self.loaded = True
            self.commanders = {}
    
    # Temporarily replace the commander_db import
    import app.nlp
    original_commander_db = getattr(app.nlp, 'commander_db', None)
    
    # Mock the commander_db
    app.nlp.commander_db = MockCommanderDB()
    
    try:
        # Test individual color detection
        result = extract_color_identity("white artifact creature")
        color_identity, is_commander_context, debug_info = result
        
        print(f"\nInput: 'white artifact creature'")
        print(f"Color identity: {color_identity}")
        print(f"Is commander context: {is_commander_context}")
        
        # Should not find any color identity (individual colors handled elsewhere)
        assert color_identity is None, f"Expected no color identity from extract_color_identity, got {color_identity}"
        assert not is_commander_context, f"Expected not commander context, got {is_commander_context}"
        
        print("✅ PASS: Individual colors don't trigger commander context")
        
    finally:
        # Restore original commander_db
        if original_commander_db:
            app.nlp.commander_db = original_commander_db

if __name__ == "__main__":
    print("🧪 Testing substring matching bug fixes...")
    print("=" * 50)
    
    test_artifact_tifa_bug()
    test_enchantment_substring_bug() 
    test_legitimate_commander_match()
    test_individual_colors_still_work()
    
    print("\n" + "=" * 50)
    print("🎉 All substring bug tests passed!")
