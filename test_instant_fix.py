#!/usr/bin/env python3

import sys
import os
sys.path.append('/root/code/mtg-nlp-app/backend/mtg-nlp-search')

from app.query_builder import extract_filters

def test_instant_queries():
    """Test queries with 'instant' to ensure proper type handling"""
    
    test_cases = [
        {
            'query': 'azorius removal instant',
            'expected_type': 'instant',
            'expected_coloridentity': 'WU',
            'description': 'Should find instant removal spells in Azorius colors'
        },
        {
            'query': 'blue instant removal',
            'expected_type': 'instant', 
            'expected_colors': 'U',
            'description': 'Should find blue instant removal spells'
        },
        {
            'query': 'creature removal',
            'expected_no_type': True,
            'expected_oracle_contains': 'creature',
            'description': 'Should find spells that remove creatures (not creature spells)'
        },
        {
            'query': 'instant counterspell',
            'expected_type': 'instant',
            'description': 'Should find instant counterspells'
        },
        {
            'query': 'sorcery removal',
            'expected_type': 'sorcery',
            'description': 'Should find sorcery removal spells'
        }
    ]
    
    print("🧪 Testing instant type handling...")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test['query']}'")
        print(f"   Expected: {test['description']}")
        
        try:
            result = extract_filters(test['query'])
            print(f"   Result: {result}")
            
            # Check expectations
            passed = True
            
            if 'expected_type' in test:
                if result.get('type') != test['expected_type']:
                    print(f"   ❌ FAIL: Expected type '{test['expected_type']}', got '{result.get('type')}'")
                    passed = False
                else:
                    print(f"   ✅ Type correct: {result.get('type')}")
            
            if 'expected_no_type' in test and test['expected_no_type']:
                if 'type' in result:
                    print(f"   ❌ FAIL: Expected no type filter, but got '{result.get('type')}'")
                    passed = False
                else:
                    print(f"   ✅ No type filter (correct)")
            
            if 'expected_coloridentity' in test:
                if result.get('coloridentity') != test['expected_coloridentity']:
                    print(f"   ❌ FAIL: Expected coloridentity '{test['expected_coloridentity']}', got '{result.get('coloridentity')}'")
                    passed = False
                else:
                    print(f"   ✅ Color identity correct: {result.get('coloridentity')}")
            
            if 'expected_colors' in test:
                if result.get('colors') != test['expected_colors']:
                    print(f"   ❌ FAIL: Expected colors '{test['expected_colors']}', got '{result.get('colors')}'")
                    passed = False
                else:
                    print(f"   ✅ Colors correct: {result.get('colors')}")
            
            if 'expected_oracle_contains' in test:
                oracle_query = result.get('scryfall_query', '')
                if test['expected_oracle_contains'] not in oracle_query:
                    print(f"   ❌ FAIL: Expected oracle to contain '{test['expected_oracle_contains']}', got '{oracle_query}'")
                    passed = False
                else:
                    print(f"   ✅ Oracle contains '{test['expected_oracle_contains']}'")
            
            if passed:
                print(f"   🎉 PASS")
            else:
                print(f"   💥 FAIL")
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test complete!")

if __name__ == "__main__":
    test_instant_queries()
