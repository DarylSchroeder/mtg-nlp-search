#!/usr/bin/env python3
"""
Test suite for API /samples endpoint queries
Tests the sample queries provided by the backend API's /samples endpoint
This is different from test_sample_queries.py which tests frontend hardcoded samples
"""

import requests
import json
import sys
from urllib.parse import quote

# Test against deployed API
BASE_URL = "https://mtg-nlp-search.onrender.com"

def test_single_query(query_text):
    """Test a single sample query"""
    try:
        # Test the search endpoint
        params = {'prompt': query_text, 'page': 1, 'per_page': 3}
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get('results', []))
            print(f"✅ \"{query_text}\" - {results_count} results")
            return True
        else:
            print(f"❌ \"{query_text}\" - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ \"{query_text}\" - Error: {str(e)[:50]}...")
        return False

def test_sample_queries():
    """Test all sample queries from the /samples endpoint"""
    print("🧪 MTG NLP Search - API Samples Test Suite")
    print("=" * 60)
    
    try:
        # Get samples from API
        response = requests.get(f"{BASE_URL}/samples")
        if response.status_code != 200:
            print(f"❌ Failed to get samples: {response.status_code}")
            return False
            
        samples_data = response.json()
        
        # Count total queries
        total_queries = 0
        for key, queries in samples_data.items():
            if key != 'note' and isinstance(queries, list):
                total_queries += len(queries)
        
        print(f"📋 Found {total_queries} sample queries in {len([k for k in samples_data.keys() if k != 'note'])} categories")
        print()
        
        all_passed = True
        total_tests = 0
        passed_tests = 0
        
        # Test each category
        for category_key, queries in samples_data.items():
            if category_key == 'note' or not isinstance(queries, list):
                continue
                
            category_name = category_key.replace('_', ' ').title()
            print(f"📂 {category_name}")
            print()
            
            for query in queries:
                total_tests += 1
                test_passed = test_single_query(query)
                if test_passed:
                    passed_tests += 1
                else:
                    all_passed = False
                print()
        
        print("=" * 60)
        print(f"📊 API SAMPLES TESTS: {passed_tests}/{total_tests} passed")
        
        if all_passed:
            print("🎉 ALL API SAMPLE QUERIES EXECUTED SUCCESSFULLY!")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} API sample queries failed.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing samples: {e}")
        return False

def test_deep_links():
    """Test deep link functionality with sample queries"""
    print("\n🔗 Testing Deep Links")
    print("=" * 30)
    
    deep_link_queries = [
        "1 mana counterspell",
        "2 cmc rakdos instant", 
        "fetchland"
    ]
    
    for query in deep_link_queries:
        encoded_query = quote(query)
        try:
            response = requests.get(f"{BASE_URL}/search?q={encoded_query}")
            if response.status_code == 200:
                data = response.json()
                results_count = len(data.get('results', []))
                print(f"🔍 Testing deep link: ?q={encoded_query}")
                print(f"   ✅ {results_count} results returned")
            else:
                print(f"🔍 Testing deep link: ?q={encoded_query}")
                print(f"   ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"🔍 Testing deep link: ?q={encoded_query}")
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("MTG NLP Search - Sample Query Validator")
    print("=" * 50)
    
    success = test_sample_queries()
    test_deep_links()
    
    sys.exit(0 if success else 1)
