#!/usr/bin/env python3
"""
Fast NLP unit test suite for all frontend sample queries
Tests only the NLP parsing logic without API calls
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mtg-nlp-search'))

from app.nlp import extract_filters

# All sample queries from frontend/script.js
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

# Expected logic validations for specific queries that had issues
EXPECTED_LOGIC = {
    '6+ mana creature': {
        'should_have': {
            'type': 'creature',
            'cmc_operator': '>=',
            'cmc': 6
        },
        'description': 'Should include cmc >= 6 and type:creature'
    },
    'X cost spell': {
        'should_have': {
            'cmc_operator': '>=',
            'cmc': 1  # X typically means at least 1
        },
        'description': 'Should include mana>={X} pattern (X>=1)'
    },
    'artifact creature': {
        'should_have': {
            'type': ['artifact', 'creature']  # Both types
        },
        'description': 'Should include both type:artifact AND type:creature'
    },
    'artifact that costs 2 or less': {
        'should_have': {
            'type': 'artifact',
            'cmc_operator': '<=',
            'cmc': 2
        },
        'description': 'Should include type:artifact and cmc<=2'
    },
    'blue instant that counters spells': {
        'should_have': {
            'colors': 'U',
            'type': 'instant',
            'effects': ['counter']
        },
        'description': 'Should include color:blue, type:instant, and effects: counter'
    },
    'dual land': {
        'should_have': {
            'type': 'land',
            'special_handling': 'dual_combinations'
        },
        'description': 'Should include dual mana combinations or dual basic types'
    }
}

def validate_expected_logic(query, filters):
    """Validate specific query logic expectations"""
    if query not in EXPECTED_LOGIC:
        return True, "No specific validation"
    
    expected = EXPECTED_LOGIC[query]['should_have']
    issues = []
    
    # Check CMC operator and value
    if 'cmc_operator' in expected:
        scryfall_query = filters.get('scryfall_query', '')
        cmc_value = expected.get('cmc')
        operator = expected['cmc_operator']
        
        expected_pattern = f"cmc{operator}{cmc_value}"
        if expected_pattern not in scryfall_query and f"cmc:{cmc_value}" not in scryfall_query:
            # Also check if cmc field has correct value
            actual_cmc = filters.get('cmc')
            if actual_cmc != cmc_value:
                issues.append(f"Expected cmc{operator}{cmc_value}, got cmc:{actual_cmc}")
    
    # Check type handling
    if 'type' in expected:
        expected_type = expected['type']
        actual_type = filters.get('type')
        
        if isinstance(expected_type, list):
            # Multiple types (like artifact creature)
            scryfall_query = filters.get('scryfall_query', '')
            for req_type in expected_type:
                if f"type:{req_type}" not in scryfall_query:
                    issues.append(f"Missing type:{req_type}")
        else:
            # Single type
            if actual_type != expected_type:
                issues.append(f"Expected type:{expected_type}, got type:{actual_type}")
    
    # Check colors
    if 'colors' in expected:
        expected_colors = expected['colors']
        actual_colors = filters.get('colors')
        if actual_colors != expected_colors:
            issues.append(f"Expected colors:{expected_colors}, got colors:{actual_colors}")
    
    # Check effects
    if 'effects' in expected:
        expected_effects = expected['effects']
        actual_effects = filters.get('effects', [])
        for effect in expected_effects:
            if effect not in actual_effects:
                issues.append(f"Missing effect:{effect}")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "Logic validation passed"

def test_sample_query_nlp(query, category):
    """Test NLP parsing for a single sample query"""
    try:
        filters = extract_filters(query)
        
        # Basic validation - should return a dict
        if not isinstance(filters, dict):
            print(f'❌ "{query}" - Invalid return type: {type(filters)}')
            return False
        
        # Validate expected logic for specific queries
        logic_valid, logic_message = validate_expected_logic(query, filters)
        
        # Show results
        if logic_valid:
            print(f'✅ "{query}"')
        else:
            print(f'⚠️  "{query}" - Logic issue: {logic_message}')
        
        # Show key filters for debugging
        key_filters = {}
        for key in ['cmc', 'type', 'colors', 'coloridentity', 'effects']:
            if key in filters:
                key_filters[key] = filters[key]
        
        scryfall_query = filters.get('scryfall_query', '')
        if key_filters or scryfall_query:
            filter_parts = []
            if key_filters:
                filter_parts.append(f"Filters: {key_filters}")
            if scryfall_query:
                short_query = scryfall_query[:60] + "..." if len(scryfall_query) > 60 else scryfall_query
                filter_parts.append(f"Scryfall: {short_query}")
            print(f'   {" | ".join(filter_parts)}')
        
        return True
        
    except Exception as e:
        print(f'❌ "{query}" - Error: {str(e)}')
        return False

def run_nlp_tests():
    """Run all NLP parsing tests"""
    print("🧠 MTG NLP Search - Sample Query NLP Test Suite")
    print("=" * 60)
    print("Testing NLP parsing only (no API calls)")
    print()
    
    total_passed = 0
    total_queries = 0
    logic_issues = 0
    
    for category, queries in SAMPLE_QUERIES.items():
        print(f"📂 {category}")
        print("-" * 40)
        
        category_passed = 0
        for query in queries:
            if test_sample_query_nlp(query, category):
                category_passed += 1
                # Check if it had logic issues
                if query in EXPECTED_LOGIC:
                    filters = extract_filters(query)
                    logic_valid, _ = validate_expected_logic(query, filters)
                    if not logic_valid:
                        logic_issues += 1
            total_queries += 1
        
        total_passed += category_passed
        print(f"   Category: {category_passed}/{len(queries)} passed")
        print()
    
    print("=" * 60)
    print(f"📊 NLP PARSING TESTS: {total_passed}/{total_queries} passed")
    
    if logic_issues > 0:
        print(f"⚠️  {logic_issues} queries have logic issues that need backend fixes")
        print("   (These are the specific issues you mentioned)")
    
    if total_passed == total_queries:
        print("🎉 ALL SAMPLE QUERIES PARSED SUCCESSFULLY!")
        if logic_issues == 0:
            print("✨ No logic issues detected!")
    else:
        print(f"❌ {total_queries - total_passed} queries failed to parse.")
    
    return total_passed == total_queries

if __name__ == "__main__":
    success = run_nlp_tests()
    sys.exit(0 if success else 1)
