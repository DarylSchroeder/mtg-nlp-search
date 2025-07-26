#!/usr/bin/env python3

import sys
sys.path.append('/root/code/mtg-nlp-app/backend/mtg-nlp-search')

from app.query_builder import extract_filters
from app.scryfall import build_query

def test_specific_query():
    """Test the specific failing query"""
    
    query = "azorius removal instant"
    print(f"🔍 Testing query: '{query}'")
    print("=" * 50)
    
    # Extract filters
    filters = extract_filters(query)
    print(f"📝 Extracted filters: {filters}")
    
    # Build Scryfall query
    scryfall_query = build_query(filters)
    print(f"🔎 Scryfall query: {scryfall_query}")
    
    # Check what we expect
    print("\n✅ Expected behavior:")
    print("- Should have type:instant (looking for instant spells)")
    print("- Should have coloridentity:WU (Azorius colors)")
    print("- Should have removal oracle text")
    print("- Should NOT have o:instant (oracle text search)")
    
    print("\n🧪 Validation:")
    
    # Check type
    if filters.get('type') == 'instant':
        print("✅ Type filter correct: instant")
    else:
        print(f"❌ Type filter wrong: {filters.get('type')}")
    
    # Check color identity
    if filters.get('coloridentity') == 'WU':
        print("✅ Color identity correct: WU")
    else:
        print(f"❌ Color identity wrong: {filters.get('coloridentity')}")
    
    # Check that we don't have o:instant in the query
    if 'o:instant' not in scryfall_query:
        print("✅ No oracle text search for 'instant'")
    else:
        print("❌ Found unwanted 'o:instant' in query")
    
    # Check that we have type:instant in the query
    if 'type:instant' in scryfall_query:
        print("✅ Has type:instant filter")
    else:
        print("❌ Missing type:instant filter")
    
    print(f"\n🎯 Final Scryfall query: {scryfall_query}")

if __name__ == "__main__":
    test_specific_query()
