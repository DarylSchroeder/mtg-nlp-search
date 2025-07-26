#!/usr/bin/env python3

import sys
sys.path.append('/root/code/mtg-nlp-app/backend/mtg-nlp-search')

from app.query_builder import extract_filters

def test_artifact_removal():
    """Test artifact removal query"""
    
    query = "blue artifact removal"
    print(f"🔍 Testing query: '{query}'")
    print("=" * 50)
    
    # Extract filters
    filters = extract_filters(query)
    print(f"📝 Extracted filters: {filters}")
    
    # Expected result from test
    expected_query = "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:artifact or o:permanent)"
    
    print(f"\n🎯 Expected oracle query: {expected_query}")
    print(f"🔍 Actual oracle query:   {filters.get('scryfall_query', 'None')}")
    
    if filters.get('scryfall_query') == expected_query:
        print("✅ Oracle query matches expected")
    else:
        print("❌ Oracle query does not match expected")
    
    # Check that type filter is removed (should target artifacts, not be artifact spells)
    if 'type' not in filters:
        print("✅ Type filter correctly removed (targeting artifacts, not artifact spells)")
    else:
        print(f"❌ Type filter should be removed, but found: {filters.get('type')}")

if __name__ == "__main__":
    test_artifact_removal()
