#!/usr/bin/env python3
"""
Test suite for frontend sample queries
Tests all sample queries used in the frontend interface
"""

import requests
import json
import sys

API_URL = 'https://mtg-nlp-search.onrender.com/search'

# Sample queries from frontend/script.js
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
        'azorius counterspell',
        'simic ramp',
        'rakdos removal',
        'selesnya tokens',
        'izzet draw'
    ],
    'Commander Context': [
        'counterspell for my Chulane deck',
        'removal for Atraxa',
        'ramp for my Omnath deck',
        'white fetchland for Chulane',
        'blue shockland for my Chulane deck'
    ],
    'Advanced Queries': [
        'blue instant that counters spells',
        'green creature with trample',
        'artifact that costs 2 or less',
        'red sorcery that deals damage',
        'white enchantment that gains life'
    ]
}

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
            
            print(f'✅ "{query}" - {results_count} results')
            
            # Show filters for debugging
            filters = data.get('filters', {})
            if filters:
                filter_summary = []
                for key, value in filters.items():
                    if key == 'scryfall_query':
                        filter_summary.append(f'{key}: "{value[:50]}..."')
                    else:
                        filter_summary.append(f'{key}: {value}')
                print(f'   Filters: {", ".join(filter_summary)}')
            
            return True
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
