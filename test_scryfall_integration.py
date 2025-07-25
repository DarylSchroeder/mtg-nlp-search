#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mtg-nlp-search'))

from app.scryfall import build_query

def test_scryfall_integration():
    """Test that Scryfall query building handles coloridentity_exact correctly"""
    
    test_cases = [
        # Regular color identity (subset matching)
        ({"coloridentity": "WU", "effects": ["removal"]}, "coloridentity:WU"),
        
        # Exact color identity (exact matching)
        ({"coloridentity_exact": "WU", "effects": ["removal"]}, "coloridentity=WU"),
        
        # Both types (should include both)
        ({"coloridentity": "UG", "coloridentity_exact": "WU", "type": "creature"}, "coloridentity:UG coloridentity=WU"),
        
        # CMC with exact color identity
        ({"cmc": 2, "coloridentity_exact": "GWU"}, "cmc:2 coloridentity=GWU"),
    ]
    
    print("Testing Scryfall query building with :only functionality\n")
    
    for filters, expected_contains in test_cases:
        query = build_query(filters)
        
        print(f"Filters: {filters}")
        print(f"Query:   {query}")
        print(f"Expected to contain: {expected_contains}")
        
        contains_expected = expected_contains in query
        status = "✅ PASS" if contains_expected else "❌ FAIL"
        print(f"Status:  {status}\n")

if __name__ == "__main__":
    test_scryfall_integration()
