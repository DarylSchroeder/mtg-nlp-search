#!/usr/bin/env python3
"""
Comprehensive test suite for color vs color identity distinction
Tests both positive cases (should use color:) and negative cases (should use coloridentity:)
"""

import requests
import json
import sys
import time
import re

API_URL = "https://mtg-nlp-search.onrender.com/search"

def colors_match(expected_query_type, actual_query):
    """Check if color sets match regardless of order"""
    
    # Extract color pattern from expected (e.g., "coloridentity:WU" -> "WU")
    expected_match = re.search(r'coloridentity:([WUBRG]+)', expected_query_type)
    if not expected_match:
        # Fallback for non-color queries (like "type:artifact")
        return expected_query_type in actual_query
    
    expected_color_set = set(expected_match.group(1))
    
    # Extract color pattern from actual query
    actual_match = re.search(r'coloridentity:([WUBRG]+)', actual_query)
    if not actual_match:
        return False
    
    actual_color_set = set(actual_match.group(1))
    
    return expected_color_set == actual_color_set

def test_query(query, expected_field, expected_query_type, description):
    """Test a query and verify it uses the correct field and query type"""
    
    print(f"\n🔍 Testing: '{query}'")
    print(f"📝 Expected: {description}")
    print("-" * 50)
    
    try:
        params = {'prompt': query, 'page': 1, 'per_page': 3}
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return False
        
        data = response.json()
        filters = data.get('filters', {})
        scryfall_query = data.get('scryfall_query', '')
        results_count = data.get('pagination', {}).get('total_results', 0)
        
        # For direct scryfall queries, check the query string
        if 'scryfall_query' in filters:
            field_present = True  # Direct queries are always valid
            query_correct = colors_match(expected_query_type, filters['scryfall_query'])
        else:
            # For filter-based queries, check the filters
            field_present = expected_field in filters
            query_correct = colors_match(expected_query_type, scryfall_query)
        
        print(f"🎛️  Filters: {json.dumps(filters, indent=2)}")
        print(f"🔍 Scryfall Query: '{scryfall_query}'")
        print(f"📦 Results: {results_count} cards")
        
        # Validation
        if field_present and query_correct:
            print(f"✅ PASS: Uses {expected_field} and {expected_query_type}")
            
            # Show first few results for context
            results = data.get('results', [])
            if results:
                print(f"🃏 Sample results:")
                for i, card in enumerate(results[:2]):
                    colors = card.get('colors', [])
                    color_identity = card.get('color_identity', [])
                    print(f"  {i+1}. {card['name']} - Colors: {colors} - CI: {color_identity}")
            
            return True
        else:
            print(f"❌ FAIL:")
            if not field_present:
                print(f"   Expected field '{expected_field}' not found in filters")
            if not query_correct:
                print(f"   Expected query type '{expected_query_type}' not found in scryfall query")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_test_suite():
    """Run comprehensive test suite for color vs color identity"""
    
    print("🧪 MTG NLP Search - Color vs Color Identity Test Suite")
    print("=" * 60)
    
    test_cases = [
        # POSITIVE CASES - Should use color: (actual card color)
        {
            'query': '1 cmc white artifact',
            'expected_field': 'colors',
            'expected_query_type': 'color:W',
            'description': 'Artifact with specific color should use color:'
        },
        {
            'query': 'blue creature 3 mana',
            'expected_field': 'colors', 
            'expected_query_type': 'color:U',
            'description': 'Creature with specific color should use color:'
        },
        {
            'query': 'red instant 2 cmc',
            'expected_field': 'colors',
            'expected_query_type': 'color:R',
            'description': 'Instant with specific color should use color:'
        },
        {
            'query': 'green sorcery',
            'expected_field': 'colors',
            'expected_query_type': 'color:G',
            'description': 'Sorcery with specific color should use color:'
        },
        {
            'query': 'black enchantment',
            'expected_field': 'colors',
            'expected_query_type': 'color:B',
            'description': 'Enchantment with specific color should use color:'
        },
        
        # NEGATIVE CASES - Should use coloridentity: (Commander deck building)
        {
            'query': 'azorius counterspell',
            'expected_field': 'coloridentity',
            'expected_query_type': 'coloridentity:WU',
            'description': 'Guild name should use coloridentity: for deck building'
        },
        {
            'query': 'simic ramp',
            'expected_field': 'coloridentity', 
            'expected_query_type': 'coloridentity:GU',
            'description': 'Guild name should use coloridentity: for deck building'
        },
        {
            'query': 'counterspell for my Chulane deck',
            'expected_field': 'coloridentity',
            'expected_query_type': 'coloridentity:GWU',
            'description': 'Commander deck context should use coloridentity:'
        },
        {
            'query': 'removal for Atraxa',
            'expected_field': 'coloridentity',
            'expected_query_type': 'coloridentity:WUBG', 
            'description': 'Commander name should use coloridentity:'
        },
        {
            'query': 'white fetchland',
            'expected_field': 'scryfall_query',  # Direct query
            'expected_query_type': 'coloridentity:W',
            'description': 'Land types should use coloridentity: for deck building'
        },
        {
            'query': 'blue shockland',
            'expected_field': 'scryfall_query',  # Direct query
            'expected_query_type': 'coloridentity:U', 
            'description': 'Land types should use coloridentity: for deck building'
        },
        
        # EDGE CASES
        {
            'query': 'white commander',
            'expected_field': 'scryfall_query',  # Direct query
            'expected_query_type': 'coloridentity:W',
            'description': 'Commander queries should use coloridentity:'
        },
        {
            'query': 'multicolor artifact',
            'expected_field': 'type',  # Should not have color field for "multicolor"
            'expected_query_type': 'type:artifact',
            'description': 'Multicolor without specific colors should not add color filter'
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        success = test_query(
            test_case['query'],
            test_case['expected_field'], 
            test_case['expected_query_type'],
            test_case['description']
        )
        
        if success:
            passed += 1
        else:
            failed += 1
        
        time.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Color vs Color Identity logic is working correctly.")
    else:
        print(f"⚠️  {failed} tests failed. Review the logic for failed cases.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
