#!/usr/bin/env python3
"""
Comprehensive test suite for all ~52 sample queries from the frontend
Verifies that NLP parsing produces expected results for each query
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mtg-nlp-search'))

from app.nlp import extract_filters

# All sample queries from the frontend organized by category
SAMPLE_QUERIES = {
    'Basic Searches': [
        '1 mana counterspell',
        '2 cmc rakdos instant', 
        'fetchland',
        '4 cost red creature',
        '3 mana simic creature',
        'red burn spell'
    ],
    'Mana Costs': [
        '2 mana instant',
        '4 cost artifact',
        '0 mana spell',
        '6+ mana creature',  # FIXED: Now handles >=6
        'X cost spell'       # FIXED: Now handles >=1
    ],
    'Guild Colors': [
        # 'azorius:only removal' - REMOVED (no longer supported)
        'azorius counterspell',
        'simic ramp',
        'rakdos removal',
        'selesnya token',
        'izzet draw'
    ],
    'Card Types': [
        'legendary creature',
        'artifact creature',    # FIXED: Now handles both types
        'enchantment removal',
        'planeswalker',
        'tribal instant'
    ],
    'Effects & Mechanics': [
        'counterspell',
        'card draw',
        'ramp spell',
        'removal spell',
        'token generator'
    ],
    'Land Types': [
        'shockland',
        'triome',
        'basic land',
        'dual land',           # FIXED: Now has comprehensive logic
        'utility land'
    ],
    'Commander Searches': [
        'counterspell for my Chulane deck',
        'removal for Atraxa',
        'ramp for Omnath',
        'draw for Niv-Mizzet',
        'token for Rhys'
    ],
    'Advanced Queries': [
        'blue instant that counters spells',  # FIXED: Now detects counter effect
        'green creature with trample',
        'artifact that costs 2 or less',     # FIXED: Now handles <=2
        'red sorcery that deals damage',
        'white enchantment that gains life'
    ]
}

def test_basic_searches():
    """Test basic search patterns"""
    passed = 0
    total = len(SAMPLE_QUERIES['Basic Searches'])
    
    for query in SAMPLE_QUERIES['Basic Searches']:
        try:
            filters = extract_filters(query)
            
            if query == '1 mana counterspell':
                assert filters.get('cmc') == 1
                assert 'counter' in str(filters.get('effects', [])).lower()
            elif query == '2 cmc rakdos instant':
                assert filters.get('cmc') == 2
                assert filters.get('colors') == 'BR'
                assert filters.get('type') == 'instant'
            elif query == 'fetchland':
                assert 'fetchland' in str(filters).lower()
            elif query == '4 cost red creature':
                assert filters.get('cmc') == 4
                assert filters.get('colors') == 'R'
                assert filters.get('type') == 'creature'
            elif query == '3 mana simic creature':
                assert filters.get('cmc') == 3
                assert filters.get('colors') == 'GU'
                assert filters.get('type') == 'creature'
            elif query == 'red burn spell':
                assert filters.get('colors') == 'R'
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Basic searches: {passed}/{total} tests passed")
    return passed == total

def test_mana_costs():
    """Test mana cost parsing with ranges"""
    passed = 0
    total = len(SAMPLE_QUERIES['Mana Costs'])
    
    for query in SAMPLE_QUERIES['Mana Costs']:
        try:
            filters = extract_filters(query)
            
            if query == '2 mana instant':
                assert filters.get('cmc') == 2
                assert filters.get('type') == 'instant'
            elif query == '4 cost artifact':
                assert filters.get('cmc') == 4
                assert filters.get('type') == 'artifact'
            elif query == '0 mana spell':
                assert filters.get('cmc') == 0
            elif query == '6+ mana creature':
                assert filters.get('cmc') == '>=6'  # FIXED
                assert filters.get('type') == 'creature'
            elif query == 'X cost spell':
                assert filters.get('cmc') == '>=1'  # FIXED
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Mana costs: {passed}/{total} tests passed")
    return passed == total

def test_guild_colors():
    """Test guild color identification"""
    passed = 0
    total = len(SAMPLE_QUERIES['Guild Colors'])
    
    for query in SAMPLE_QUERIES['Guild Colors']:
        try:
            filters = extract_filters(query)
            
            if query == 'azorius counterspell':
                assert filters.get('colors') == 'WU'
                assert 'counter' in str(filters.get('effects', [])).lower()
            elif query == 'simic ramp':
                assert filters.get('colors') == 'GU'
                assert 'ramp' in str(filters.get('effects', [])).lower()
            elif query == 'rakdos removal':
                assert filters.get('colors') == 'BR'
                effects = str(filters.get('effects', [])).lower()
                assert any(word in effects for word in ['destroy', 'remove', 'removal'])
            elif query == 'selesnya token':
                assert filters.get('colors') == 'GW'
                assert 'token' in str(filters.get('effects', [])).lower()
            elif query == 'izzet draw':
                assert filters.get('colors') == 'UR'
                assert 'draw' in str(filters.get('effects', [])).lower()
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Guild colors: {passed}/{total} tests passed")
    return passed == total

def test_card_types():
    """Test card type parsing including multi-types"""
    passed = 0
    total = len(SAMPLE_QUERIES['Card Types'])
    
    for query in SAMPLE_QUERIES['Card Types']:
        try:
            filters = extract_filters(query)
            
            if query == 'legendary creature':
                type_val = filters.get('type')
                assert 'legendary' in type_val and 'creature' in type_val
            elif query == 'artifact creature':
                type_val = filters.get('type')
                assert type_val == 'artifact creature'  # FIXED: Both types
            elif query == 'enchantment removal':
                assert filters.get('type') == 'enchantment'
                effects = str(filters.get('effects', [])).lower()
                assert any(word in effects for word in ['destroy', 'remove', 'removal'])
            elif query == 'planeswalker':
                assert filters.get('type') == 'planeswalker'
            elif query == 'tribal instant':
                type_val = filters.get('type')
                assert 'tribal' in type_val and 'instant' in type_val
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Card types: {passed}/{total} tests passed")
    return passed == total

def test_effects_mechanics():
    """Test effect and mechanic detection"""
    passed = 0
    total = len(SAMPLE_QUERIES['Effects & Mechanics'])
    
    for query in SAMPLE_QUERIES['Effects & Mechanics']:
        try:
            filters = extract_filters(query)
            effects = str(filters.get('effects', [])).lower()
            
            if query == 'counterspell':
                assert 'counter' in effects
            elif query == 'card draw':
                assert 'draw' in effects
            elif query == 'ramp spell':
                assert 'ramp' in effects
            elif query == 'removal spell':
                assert any(word in effects for word in ['destroy', 'remove', 'removal'])
            elif query == 'token generator':
                assert 'token' in effects
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Effects & mechanics: {passed}/{total} tests passed")
    return passed == total

def test_land_types():
    """Test land type parsing including dual lands"""
    passed = 0
    total = len(SAMPLE_QUERIES['Land Types'])
    
    for query in SAMPLE_QUERIES['Land Types']:
        try:
            filters = extract_filters(query)
            
            if query == 'shockland':
                assert 'shock' in str(filters).lower()
            elif query == 'triome':
                assert 'triome' in str(filters).lower() or 'triland' in str(filters).lower()
            elif query == 'basic land':
                assert filters.get('type') == 'basic land' or filters.get('type') == 'land'
            elif query == 'dual land':
                # FIXED: Should have comprehensive dual land logic
                scryfall_query = filters.get('scryfall_query', '')
                assert 'o:{' in scryfall_query and 'and' in scryfall_query
            elif query == 'utility land':
                assert filters.get('type') == 'land'
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Land types: {passed}/{total} tests passed")
    return passed == total

def test_commander_searches():
    """Test commander-specific searches with color identity"""
    passed = 0
    total = len(SAMPLE_QUERIES['Commander Searches'])
    
    for query in SAMPLE_QUERIES['Commander Searches']:
        try:
            filters = extract_filters(query)
            
            if query == 'counterspell for my Chulane deck':
                assert 'counter' in str(filters.get('effects', [])).lower()
                color_id = filters.get('coloridentity')
                assert color_id and set('GWU').issubset(set(color_id))
            elif query == 'removal for Atraxa':
                effects = str(filters.get('effects', [])).lower()
                assert any(word in effects for word in ['destroy', 'remove', 'removal'])
                color_id = filters.get('coloridentity')
                assert color_id and set('WUBG').issubset(set(color_id))
            elif query == 'ramp for Omnath':
                assert 'ramp' in str(filters.get('effects', [])).lower()
            elif query == 'draw for Niv-Mizzet':
                assert 'draw' in str(filters.get('effects', [])).lower()
            elif query == 'token for Rhys':
                assert 'token' in str(filters.get('effects', [])).lower()
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Commander searches: {passed}/{total} tests passed")
    return passed == total

def test_advanced_queries():
    """Test advanced query parsing with multiple constraints"""
    passed = 0
    total = len(SAMPLE_QUERIES['Advanced Queries'])
    
    for query in SAMPLE_QUERIES['Advanced Queries']:
        try:
            filters = extract_filters(query)
            
            if query == 'blue instant that counters spells':
                # FIXED: Should detect counter effect
                assert filters.get('colors') == 'U'
                assert filters.get('type') == 'instant'
                assert 'counter' in str(filters.get('effects', [])).lower()
            elif query == 'green creature with trample':
                assert filters.get('colors') == 'G'
                assert filters.get('type') == 'creature'
                assert 'trample' in str(filters.get('effects', [])).lower()
            elif query == 'artifact that costs 2 or less':
                # FIXED: Should handle <=2
                assert filters.get('type') == 'artifact'
                assert filters.get('cmc') == '<=2'
            elif query == 'red sorcery that deals damage':
                assert filters.get('colors') == 'R'
                assert filters.get('type') == 'sorcery'
                effects = str(filters.get('effects', [])).lower()
                assert any(word in effects for word in ['damage', 'deal'])
            elif query == 'white enchantment that gains life':
                assert filters.get('colors') == 'W'
                assert filters.get('type') == 'enchantment'
                effects = str(filters.get('effects', [])).lower()
                assert any(word in effects for word in ['life', 'gain'])
            
            passed += 1
            
        except Exception as e:
            print(f"❌ Failed: {query} - {e}")
    
    print(f"✅ Advanced queries: {passed}/{total} tests passed")
    return passed == total

def run_all_tests():
    """Run comprehensive tests for all sample queries"""
    print("🧪 Testing All Sample Queries - NLP Parsing")
    print("=" * 60)
    
    # Count total queries
    total_queries = sum(len(queries) for queries in SAMPLE_QUERIES.values())
    print(f"📊 Total sample queries to test: {total_queries}")
    print()
    
    # Run all test categories
    results = []
    results.append(test_basic_searches())
    results.append(test_mana_costs())
    results.append(test_guild_colors())
    results.append(test_card_types())
    results.append(test_effects_mechanics())
    results.append(test_land_types())
    results.append(test_commander_searches())
    results.append(test_advanced_queries())
    
    # Summary
    passed_categories = sum(results)
    total_categories = len(results)
    
    print()
    print("=" * 60)
    if passed_categories == total_categories:
        print("🎉 ALL TESTS PASSED!")
        print(f"✅ {passed_categories}/{total_categories} categories passed")
        print()
        print("🔧 Key fixes implemented:")
        print("  • 6+ mana creature → cmc>=6")
        print("  • X cost spell → cmc>=1") 
        print("  • artifact creature → both types detected")
        print("  • artifact that costs 2 or less → cmc<=2")
        print("  • blue instant that counters spells → counter effect detected")
        print("  • dual land → comprehensive dual land logic")
        print("  • Removed azorius:only removal (no longer supported)")
        return True
    else:
        print(f"❌ {passed_categories}/{total_categories} categories passed")
        print("🔧 Some tests still need fixes")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
