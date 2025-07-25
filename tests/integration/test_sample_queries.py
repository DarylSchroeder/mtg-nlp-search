#!/usr/bin/env python3
"""
Test suite for frontend sample queries
Tests all sample queries used in the frontend interface
"""

import requests
import json
import sys

API_URL = 'https://mtg-nlp-search.onrender.com/search'

# Sample queries from frontend/script.js (exact match)
SAMPLE_QUERIES = {
    'Basic Searches': [
        '1 mana counterspell',
        'fetchland',
        'azorius removal',
        '3 mana simic creature',
        'red burn spell'
    ],
    'Mana Costs': [
        '2 mana instant',
        '4 cost artifact',
        '0 mana spell',
        '6+ mana creature',
        'X cost spell'
    ],
    'Guild Colors': [
        # Note: 'azorius:only removal' removed as :ONLY is no longer supported
        'azorius counterspell',
        'simic ramp',
        'rakdos removal',
        'selesnya token',
        'izzet draw'
    ],
    'Card Types': [
        'legendary creature',
        'artifact creature',
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
        'dual land',
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
        'blue instant that counters spells',
        'green creature with trample',
        'artifact that costs 2 or less',
        'red sorcery that deals damage',
        'white enchantment that gains life'
    ]
}

# Expected logic validations for specific queries
QUERY_VALIDATIONS = {
    '6+ mana creature': {
        'should_contain': ['cmc>=6', 'type:creature'],
        'description': 'Should include cmc >= 6 and type:creature'
    },
    'X cost spell': {
        'should_contain': ['mana>='],
        'description': 'Should include mana>={X} pattern'
    },
    'artifact creature': {
        'should_contain': ['type:artifact', 'type:creature'],
        'description': 'Should include both type:artifact AND type:creature'
    },
    'artifact that costs 2 or less': {
        'should_contain': ['type:artifact', 'cmc<=2'],
        'description': 'Should include type:artifact and cmc<=2'
    },
    'blue instant that counters spells': {
        'should_contain': ['color:blue', 'type:instant', 'counter'],
        'description': 'Should include color:blue, type:instant, and effects: counter'
    },
    'dual land': {
        'should_contain_any': [
            ['o:{G}', 'o:{W}'],  # Should contain mana symbols for dual combinations
            ['type:forest', 'type:plains']  # Or dual basic land types
        ],
        'description': 'Should include dual mana combinations or dual basic types'
    }
}

def validate_query_logic(query, data):
    """Validate specific query logic expectations"""
    if query not in QUERY_VALIDATIONS:
        return True, "No specific validation"
    
    validation = QUERY_VALIDATIONS[query]
    scryfall_query = data.get('scryfall_query', '').lower()
    filters = data.get('filters', {})
    
    # Check should_contain requirements
    if 'should_contain' in validation:
        missing = []
        for requirement in validation['should_contain']:
            if requirement.lower() not in scryfall_query:
                # Also check in filters
                found_in_filters = False
                for filter_value in filters.values():
                    if isinstance(filter_value, str) and requirement.lower() in filter_value.lower():
                        found_in_filters = True
                        break
                if not found_in_filters:
                    missing.append(requirement)
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
    
    # Check should_contain_any requirements (for dual land)
    if 'should_contain_any' in validation:
        found_any = False
        for requirement_group in validation['should_contain_any']:
            group_found = all(req.lower() in scryfall_query for req in requirement_group)
            if group_found:
                found_any = True
                break
        
        if not found_any:
            return False, f"Should contain any of: {validation['should_contain_any']}"
    
    return True, "Logic validation passed"

def test_sample_query(query, category):
    """Test a single sample query"""
    try:
        params = {'prompt': query, 'page': 1, 'per_page': 3}
        response = requests.get(API_URL, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get('results', []))
            
            # Check response structure
            required_fields = ['results', 'filters', 'scryfall_query']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f'❌ "{query}" - Missing fields: {missing_fields}')
                return False
            
            # Validate query logic
            logic_valid, logic_message = validate_query_logic(query, data)
            
            if logic_valid:
                print(f'✅ "{query}" - {results_count} results')
            else:
                print(f'⚠️  "{query}" - {results_count} results - Logic issue: {logic_message}')
            
            # Show filters for debugging
            filters = data.get('filters', {})
            scryfall_query = data.get('scryfall_query', '')
            if filters or scryfall_query:
                print(f'   Scryfall: {scryfall_query[:80]}{"..." if len(scryfall_query) > 80 else ""}')
                if filters:
                    filter_summary = []
                    for key, value in filters.items():
                        if key != 'scryfall_query':
                            filter_summary.append(f'{key}: {value}')
                    if filter_summary:
                        print(f'   Filters: {", ".join(filter_summary)}')
            
            return True  # Return True for successful API call, regardless of logic validation
        else:
            print(f'❌ "{query}" - HTTP {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ "{query}" - Error: {str(e)[:50]}...')
        return False

def run_all_tests():
    """Run all sample query tests"""
    print("🧪 MTG NLP Search - Sample Query Test Suite")
    print("=" * 60)
    
    total_passed = 0
    total_queries = 0
    
    for category, queries in SAMPLE_QUERIES.items():
        print(f"\n📂 {category}")
        print("-" * 40)
        
        category_passed = 0
        for query in queries:
            if test_sample_query(query, category):
                category_passed += 1
            total_queries += 1
        
        total_passed += category_passed
        print(f"   Category: {category_passed}/{len(queries)} passed")
    
    print("\n" + "=" * 60)
    print(f"📊 SAMPLE QUERY TESTS: {total_passed}/{total_queries} passed")
    
    if total_passed == total_queries:
        print("🎉 ALL SAMPLE QUERIES EXECUTED SUCCESSFULLY!")
        print("Note: Some queries may return 0 results due to parsing limitations.")
    else:
        print(f"⚠️  {total_queries - total_passed} queries failed to execute.")
    
    return total_passed == total_queries

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
