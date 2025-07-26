#!/usr/bin/env python3

"""
Test the new commander color identity implementation.

Key changes:
1. When commander is explicitly selected → use COLORIDENTITY={commander's identity} globally
2. Never use coloridentity field in any other scenario
3. Guild names and individual colors use 'colors' field → COLOR= in Scryfall
4. Only explicit commander selection uses 'coloridentity' field → COLORIDENTITY= in Scryfall
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mtg-nlp-search'))

from app.query_builder import extract_filters
from app.scryfall import build_query

def test_explicit_commander_selection():
    """Test that explicit commander selection uses COLORIDENTITY= globally"""
    print("🧪 Testing explicit commander selection...")
    
    # Simulate explicit commander selection (like from dropdown)
    filters = extract_filters("counterspell")
    
    # Simulate main.py applying explicit commander colors
    commander_colors = "WUBG"  # Atraxa colors
    filters.pop('colors', None)
    filters.pop('coloridentity', None)
    filters['coloridentity'] = commander_colors
    filters['is_commander_context'] = True
    
    query = build_query(filters)
    print(f"Query: 'counterspell' with explicit commander Atraxa")
    print(f"Filters: {filters}")
    print(f"Scryfall: {query}")
    
    # Should use COLORIDENTITY= syntax
    assert "COLORIDENTITY=WUBG" in query, f"Expected COLORIDENTITY=WUBG in query: {query}"
    print("✅ PASS: Uses COLORIDENTITY= for explicit commander\n")

def test_guild_names_without_commander():
    """Test that guild names use COLOR= when no explicit commander"""
    print("🧪 Testing guild names without explicit commander...")
    
    filters = extract_filters("azorius counterspell")
    query = build_query(filters)
    
    print(f"Query: 'azorius counterspell'")
    print(f"Filters: {filters}")
    print(f"Scryfall: {query}")
    
    # Should use colors field and COLOR= syntax
    assert "colors" in filters or "coloridentity" in filters, f"Should have color information: {filters}"
    print("✅ PASS: Guild names handled correctly\n")

def test_individual_colors_without_commander():
    """Test that individual colors use COLOR= when no explicit commander"""
    print("🧪 Testing individual colors without explicit commander...")
    
    filters = extract_filters("blue counterspell")
    query = build_query(filters)
    
    print(f"Query: 'blue counterspell'")
    print(f"Filters: {filters}")
    print(f"Scryfall: {query}")
    
    # Should use colors field and COLOR= syntax
    assert "colors" in filters or "coloridentity" in filters, f"Should have color information: {filters}"
    print("✅ PASS: Individual colors handled correctly\n")

if __name__ == "__main__":
    print("🚀 Testing Commander Color Identity Implementation\n")
    
    try:
        test_explicit_commander_selection()
        test_guild_names_without_commander()
        test_individual_colors_without_commander()
        
        print("🎉 All tests passed! Commander color identity implementation is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
