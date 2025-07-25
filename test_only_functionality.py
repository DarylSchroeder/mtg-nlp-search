#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mtg-nlp-search'))

from app.nlp import extract_filters_fallback

def test_only_functionality():
    """Test the new :only functionality for exact color identity matching"""
    
    test_cases = [
        # Regular guild searches (should allow subset matching)
        ("azorius removal", {"coloridentity": "WU", "effects": ["removal"]}),
        ("simic ramp", {"coloridentity": "UG", "effects": ["ramp"]}),
        
        # :only guild searches (should require exact matching)
        ("azorius:only removal", {"coloridentity_exact": "WU", "effects": ["removal"]}),
        ("simic:only creature", {"coloridentity_exact": "UG", "type": "creature"}),
        
        # Shard and wedge tests
        ("bant:only counterspell", {"coloridentity_exact": "GWU", "effects": ["counter"]}),
        ("jeskai removal", {"coloridentity": "URW", "effects": ["removal"]}),
        ("abzan:only creature", {"coloridentity_exact": "WBG", "type": "creature"}),
        
        # Commander tests
        ("chulane:only ramp", {"coloridentity_exact": "GWU", "effects": ["ramp"]}),
        ("atraxa removal", {"coloridentity": "WUBG", "effects": ["removal"]}),
    ]
    
    print("Testing :only functionality for exact color identity matching\n")
    
    for query, expected in test_cases:
        result = extract_filters_fallback(query)
        
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        
        # Check if the result matches expected
        matches = True
        for key, value in expected.items():
            if key not in result or result[key] != value:
                matches = False
                break
        
        status = "✅ PASS" if matches else "❌ FAIL"
        print(f"Status:   {status}\n")

if __name__ == "__main__":
    test_only_functionality()
