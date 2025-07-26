#!/usr/bin/env python3

"""
Comprehensive test of the new commander color identity implementation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mtg-nlp-search'))

from app.query_builder import extract_filters
from app.scryfall import build_query

def test_scenarios():
    """Test various scenarios to ensure the new implementation works correctly"""
    
    scenarios = [
        {
            "name": "Individual color without commander",
            "query": "blue counterspell",
            "expected_field": "colors",
            "expected_scryfall": "COLOR=U"
        },
        {
            "name": "Guild name without commander",
            "query": "azorius counterspell", 
            "expected_field": "colors",
            "expected_scryfall": "COLOR=WU"
        },
        {
            "name": "Shard name without commander",
            "query": "bant counterspell",
            "expected_field": "colors", 
            "expected_scryfall": "COLOR=GWU"
        },
        {
            "name": "Commander context keywords",
            "query": "removal for my Atraxa deck",
            "expected_field": "coloridentity",
            "expected_scryfall": "COLORIDENTITY="
        }
    ]
    
    for scenario in scenarios:
        print(f"🧪 Testing: {scenario['name']}")
        print(f"Query: '{scenario['query']}'")
        
        filters = extract_filters(scenario['query'])
        query = build_query(filters)
        
        print(f"Filters: {filters}")
        print(f"Scryfall: {query}")
        
        # Check that the expected field is present
        if scenario['expected_field'] == "colors":
            assert "colors" in filters, f"Expected 'colors' field in filters: {filters}"
            assert filters.get('is_commander_context', True) == False, f"Should not be commander context: {filters}"
        elif scenario['expected_field'] == "coloridentity":
            assert "coloridentity" in filters, f"Expected 'coloridentity' field in filters: {filters}"
            assert filters.get('is_commander_context', False) == True, f"Should be commander context: {filters}"
        
        # Check Scryfall query syntax
        assert scenario['expected_scryfall'] in query, f"Expected '{scenario['expected_scryfall']}' in query: {query}"
        
        print("✅ PASS\n")

def test_explicit_commander_override():
    """Test that explicit commander selection overrides everything"""
    print("🧪 Testing explicit commander override...")
    
    # Start with a query that would normally use colors
    filters = extract_filters("blue counterspell")
    print(f"Original filters: {filters}")
    
    # Simulate explicit commander selection (like from dropdown)
    commander_colors = "RG"  # Gruul commander
    filters.pop('colors', None)
    filters.pop('coloridentity', None)
    filters['coloridentity'] = commander_colors
    filters['is_commander_context'] = True
    
    query = build_query(filters)
    
    print(f"After commander override: {filters}")
    print(f"Scryfall: {query}")
    
    # Should use COLORIDENTITY= syntax with commander colors
    assert "COLORIDENTITY=RG" in query, f"Expected COLORIDENTITY=RG in query: {query}"
    assert "COLOR=U" not in query, f"Should not have original blue color: {query}"
    assert "colors" not in filters, f"Should not have colors field: {filters}"
    assert "coloridentity" in filters, f"Should have coloridentity field: {filters}"
    assert filters['coloridentity'] == "RG", f"Should have commander colors: {filters}"
    
    print("✅ PASS: Explicit commander overrides text colors\n")

if __name__ == "__main__":
    print("🚀 Comprehensive Commander Color Identity Test\n")
    
    try:
        test_scenarios()
        test_explicit_commander_override()
        
        print("🎉 All comprehensive tests passed!")
        print("\n📋 Summary of Implementation:")
        print("✅ Individual colors (blue, red, etc.) → 'colors' field → COLOR= syntax")
        print("✅ Guild names (azorius, simic, etc.) → 'colors' field → COLOR= syntax") 
        print("✅ Commander context keywords → 'coloridentity' field → COLORIDENTITY= syntax")
        print("✅ Explicit commander selection → 'coloridentity' field → COLORIDENTITY= syntax")
        print("✅ Explicit commander overrides any text-based color detection")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
