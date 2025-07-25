#!/usr/bin/env python3
"""
Test specific logic errors identified in NLP parsing
Focus on the key issues that need to be fixed
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mtg-nlp-search'))

from app.nlp import extract_filters

def test_logic_errors():
    """Test the specific logic errors identified"""
    
    print("🔍 Testing identified logic errors...")
    
    # 1. 6+ mana creature -> should include a cmc >= 6
    print("\n1. Testing '6+ mana creature'")
    filters = extract_filters("6+ mana creature")
    print(f"   Result: {filters}")
    cmc = filters.get('cmc')
    if cmc == 6:
        print("   ⚠️  Currently returns cmc:6, should be cmc>=6")
    elif cmc is None:
        print("   ❌ No CMC filter detected")
    else:
        print(f"   ✅ CMC filter: {cmc}")
    
    # 2. X cost spell -> mana>={X}
    print("\n2. Testing 'X cost spell'")
    filters = extract_filters("X cost spell")
    print(f"   Result: {filters}")
    cmc = filters.get('cmc')
    if cmc is None:
        print("   ❌ No CMC filter for X cost")
    else:
        print(f"   ✅ CMC filter: {cmc}")
    
    # 3. artifact creature -> type:artifact and type=creature
    print("\n3. Testing 'artifact creature'")
    filters = extract_filters("artifact creature")
    print(f"   Result: {filters}")
    type_val = filters.get('type')
    types_val = filters.get('types')
    if type_val == 'creature' and 'artifact' not in str(filters):
        print("   ❌ Missing artifact type")
    elif 'artifact' in str(filters) and 'creature' in str(filters):
        print("   ✅ Both types detected")
    else:
        print(f"   ⚠️  Partial detection: {type_val}, {types_val}")
    
    # 4. artifact that costs 2 or less -> type:artifact , cmc<=2
    print("\n4. Testing 'artifact that costs 2 or less'")
    filters = extract_filters("artifact that costs 2 or less")
    print(f"   Result: {filters}")
    type_val = filters.get('type')
    cmc = filters.get('cmc')
    if type_val == 'artifact' and cmc == 2:
        print("   ⚠️  Returns cmc:2, should be cmc<=2")
    elif type_val == 'artifact' and cmc is None:
        print("   ❌ Missing CMC constraint")
    else:
        print(f"   Status: type={type_val}, cmc={cmc}")
    
    # 5. blue instant that counters spells -> should have effects: counter
    print("\n5. Testing 'blue instant that counters spells'")
    filters = extract_filters("blue instant that counters spells")
    print(f"   Result: {filters}")
    colors = filters.get('colors')
    type_val = filters.get('type')
    effects = filters.get('effects', [])
    has_counter = 'counter' in str(effects).lower()
    
    if colors == 'U' and type_val == 'instant' and has_counter:
        print("   ✅ All components detected correctly")
    else:
        print(f"   Status: colors={colors}, type={type_val}, counter={has_counter}")
    
    # 6. dual land -> should include dual land logic
    print("\n6. Testing 'dual land'")
    filters = extract_filters("dual land")
    print(f"   Result: {filters}")
    if 'dual' in str(filters).lower() or 'land' in str(filters).lower():
        print("   ✅ Land detection present")
    else:
        print("   ❌ No dual land logic detected")

def test_sample_queries_structure():
    """Test a few sample queries to understand current structure"""
    
    print("\n🧪 Testing sample query structure...")
    
    test_queries = [
        "1 mana counterspell",
        "azorius counterspell", 
        "artifact creature",
        "fetchland",
        "counterspell for my Chulane deck"
    ]
    
    for query in test_queries:
        filters = extract_filters(query)
        print(f"\nQuery: '{query}'")
        print(f"Result: {filters}")
        
        # Analyze structure
        keys = list(filters.keys())
        print(f"Keys: {keys}")

def run_tests():
    """Run all logic error tests"""
    print("🔧 NLP Logic Error Analysis")
    print("=" * 50)
    
    test_logic_errors()
    test_sample_queries_structure()
    
    print("\n" + "=" * 50)
    print("📋 Summary of Issues to Fix:")
    print("  1. 6+ mana creature: Need >= logic for CMC")
    print("  2. X cost spell: Need X cost handling")
    print("  3. artifact creature: Need multi-type support")
    print("  4. 'costs X or less': Need <= logic for CMC")
    print("  5. Counter effects: Verify effect detection")
    print("  6. Dual lands: Need comprehensive dual land logic")

if __name__ == "__main__":
    run_tests()
