#!/usr/bin/env python3
"""
Test script to validate all sample queries return expected results.
This ensures the /samples endpoint only contains working examples.
"""

import requests
import json
import sys
from urllib.parse import quote

# Test against local server (change to deployed URL for production testing)
BASE_URL = "http://localhost:8001"
# BASE_URL = "https://mtg-nlp-search.onrender.com"

def test_sample_queries():
    """Test all sample queries from the /samples endpoint"""
    print("🧪 Testing Sample Queries")
    print("=" * 50)
    
    try:
        # Get samples from API
        response = requests.get(f"{BASE_URL}/samples")
        if response.status_code != 200:
            print(f"❌ Failed to get samples: {response.status_code}")
            return False
            
        samples_data = response.json()
        print(f"📋 Found {samples_data['total_queries']} sample queries in {samples_data['total_categories']} categories")
        print()
        
        all_passed = True
        total_tests = 0
        passed_tests = 0
        
        for category in samples_data['samples']:
            print(f"📂 {category['category']}")
            print(f"   {category['description']}")
            print()
            
            for query in category['queries']:
                total_tests += 1
                test_passed = test_single_query(query)
                if test_passed:
                    passed_tests += 1
                else:
                    all_passed = False
                print()
        
        print("=" * 50)
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        
        if all_passed:
            print("✅ All sample queries are working correctly!")
            return True
        else:
            print("❌ Some sample queries failed - update needed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing samples: {e}")
        return False

def test_single_query(query_info):
    """Test a single sample query"""
    query_text = query_info['text']
    expected_min = query_info['expected_min']
    expected_max = query_info['expected_max']
    description = query_info['description']
    
    print(f"   🔍 Testing: \"{query_text}\"")
    print(f"      Expected: {expected_min}-{expected_max} results")
    
    try:
        # Test the search API
        encoded_query = quote(query_text)
        response = requests.get(f"{BASE_URL}/search?prompt={encoded_query}&per_page=100")
        
        if response.status_code != 200:
            print(f"      ❌ API Error: {response.status_code}")
            return False
            
        data = response.json()
        
        if 'error' in data:
            print(f"      ❌ Search Error: {data['error']}")
            return False
            
        actual_results = data['pagination']['total_results']
        scryfall_query = data.get('scryfall_query', 'N/A')
        
        # Check if results are within expected range
        if expected_min <= actual_results <= expected_max:
            print(f"      ✅ {actual_results} results (within range)")
            print(f"      🔧 Scryfall query: {scryfall_query}")
            
            # Show a few example results
            if data['results']:
                examples = [card['name'] for card in data['results'][:3]]
                print(f"      📋 Examples: {', '.join(examples)}")
            
            return True
        else:
            print(f"      ❌ {actual_results} results (outside range {expected_min}-{expected_max})")
            print(f"      🔧 Scryfall query: {scryfall_query}")
            
            # Show what we got to help debug
            if data['results']:
                examples = [card['name'] for card in data['results'][:5]]
                print(f"      📋 Got: {', '.join(examples)}")
            
            return False
            
    except Exception as e:
        print(f"      ❌ Exception: {e}")
        return False

def test_deep_links():
    """Test that deep links work correctly"""
    print("\n🔗 Testing Deep Links")
    print("=" * 30)
    
    # Test a few sample deep link formats
    test_links = [
        "1%20mana%20counterspell",
        "2%20cmc%20rakdos%20instant", 
        "fetchland"
    ]
    
    for encoded_query in test_links:
        print(f"🔍 Testing deep link: ?q={encoded_query}")
        
        try:
            response = requests.get(f"{BASE_URL}/search?prompt={encoded_query}")
            if response.status_code == 200:
                data = response.json()
                results = data['pagination']['total_results']
                print(f"   ✅ {results} results returned")
            else:
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("MTG NLP Search - Sample Query Validator")
    print("=" * 50)
    
    # Test samples
    samples_passed = test_sample_queries()
    
    # Test deep links
    test_deep_links()
    
    # Exit with appropriate code
    sys.exit(0 if samples_passed else 1)
