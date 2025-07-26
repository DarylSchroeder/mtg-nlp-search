#!/usr/bin/env python3
"""
Test removal vs graveyard hate disambiguation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mtg-nlp-search'))

from app.query_builder import extract_filters

def test_removal_vs_graveyard_hate():
    """Test that removal and graveyard hate are properly distinguished"""
    
    test_cases = [
        # True removal - should match removal pattern
        {
            'query': 'azorius removal',
            'expected_type': 'removal',
            'should_contain': ['destroy', 'exile', 'put into', 'creature', 'artifact', 'enchantment', 'planeswalker', 'permanent'],
            'should_not_contain': ['graveyard']
        },
        {
            'query': 'blue artifact removal', 
            'expected_type': 'removal',
            'should_contain': ['destroy', 'exile', 'put into', 'artifact', 'permanent'],
            'should_not_contain': ['graveyard']
        },
        
        # Graveyard hate - should match graveyard_hate pattern
        {
            'query': 'graveyard hate',
            'expected_type': 'graveyard_hate', 
            'should_contain': ['exile', 'graveyard'],
            'should_not_contain': ['creature', 'artifact', 'enchantment']
        },
        {
            'query': 'exile graveyard',
            'expected_type': 'graveyard_hate',
            'should_contain': ['exile', 'graveyard'],
            'should_not_contain': ['creature', 'artifact']
        },
        
        # Edge cases that should NOT match removal
        {
            'query': 'exile all graveyards',  # This is what Abstergo Entertainment does
            'expected_type': 'graveyard_hate',
            'should_contain': ['exile', 'graveyard'],
            'should_not_contain': ['creature', 'artifact', 'enchantment', 'permanent']
        }
    ]
    
    print("🧪 Testing Removal vs Graveyard Hate Disambiguation")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected_type = test_case['expected_type']
        
        print(f"\n{i}. Testing: '{query}'")
        
        result = extract_filters(query)
        scryfall_query = result.get('scryfall_query', '').lower()
        
        print(f"   Result: {result}")
        print(f"   Scryfall: {scryfall_query}")
        
        # Check that we got a scryfall_query
        if not scryfall_query:
            print(f"   ❌ FAIL: No scryfall_query generated")
            continue
            
        # Check should_contain items
        missing_items = []
        for item in test_case['should_contain']:
            if item.lower() not in scryfall_query:
                missing_items.append(item)
        
        # Check should_not_contain items  
        unwanted_items = []
        for item in test_case['should_not_contain']:
            if item.lower() in scryfall_query:
                unwanted_items.append(item)
        
        if missing_items:
            print(f"   ❌ FAIL: Missing required terms: {missing_items}")
        elif unwanted_items:
            print(f"   ❌ FAIL: Contains unwanted terms: {unwanted_items}")
        else:
            print(f"   ✅ PASS: Correctly identified as {expected_type}")

def test_specific_cards():
    """Test queries that should/shouldn't match specific problematic cards"""
    
    print("\n🎯 Testing Specific Card Scenarios")
    print("=" * 40)
    
    # Test the Abstergo Entertainment case
    print("\n1. Testing 'azorius removal' should NOT match 'exile all graveyards'")
    result = extract_filters('azorius removal')
    scryfall_query = result.get('scryfall_query', '').lower()
    
    print(f"   Query: {scryfall_query}")
    
    # This should require exile + (creature/artifact/enchantment/planeswalker/permanent)
    # "exile all graveyards" should NOT match because it doesn't have permanent types
    has_exile = 'exile' in scryfall_query
    has_permanent_types = any(ptype in scryfall_query for ptype in ['creature', 'artifact', 'enchantment', 'planeswalker', 'permanent'])
    excludes_graveyard_only = 'graveyard' not in scryfall_query or has_permanent_types
    
    if has_exile and has_permanent_types and excludes_graveyard_only:
        print("   ✅ PASS: Query properly requires permanent types with exile")
    else:
        print(f"   ❌ FAIL: has_exile={has_exile}, has_permanent_types={has_permanent_types}, excludes_graveyard_only={excludes_graveyard_only}")

if __name__ == "__main__":
    test_removal_vs_graveyard_hate()
    test_specific_cards()
    print("\n" + "=" * 60)
    print("🏁 Removal proximity testing complete!")
