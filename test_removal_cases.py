#!/usr/bin/env python3

import sys
sys.path.append('/root/code/mtg-nlp-app/backend/mtg-nlp-search')

from app.query_builder import extract_filters

def test_removal_cases():
    """Test different removal cases"""
    
    test_cases = [
        {
            'query': 'azorius removal instant',
            'expected_type': 'instant',
            'expected_coloridentity': 'WU',
            'description': 'Should find instant removal spells in Azorius colors'
        },
        {
            'query': 'blue artifact removal',
            'expected_oracle': '(o:destroy or o:"put into" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:artifact or o:permanent)',
            'expected_colors': 'U',
            'description': 'Should find blue spells that remove artifacts (with permanent clause)'
        },
        {
            'query': 'land removal',
            'expected_oracle': '(o:destroy or o:"put into" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and o:land',
            'description': 'Should find spells that remove lands (no permanent clause for land)'
        },
        {
            'query': 'creature removal',
            'expected_oracle': '(o:destroy or o:"put into" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:creature or o:permanent)',
            'description': 'Should find spells that remove creatures (with permanent clause)'
        }
    ]
    
    print("🧪 Testing removal cases...")
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
            
            if 'expected_oracle' in test:
                oracle_query = result.get('scryfall_query', '')
                if oracle_query != test['expected_oracle']:
                    print(f"   ❌ FAIL: Oracle query mismatch")
                    print(f"      Expected: {test['expected_oracle']}")
                    print(f"      Got:      {oracle_query}")
                    passed = False
                else:
                    print(f"   ✅ Oracle query correct")
            
            if passed:
                print(f"   🎉 PASS")
            else:
                print(f"   💥 FAIL")
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test complete!")

if __name__ == "__main__":
    test_removal_cases()
