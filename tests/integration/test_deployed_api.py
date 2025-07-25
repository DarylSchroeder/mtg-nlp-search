#!/usr/bin/env python3
"""
Test suite for deployed API endpoints
Tests the live API at https://mtg-nlp-search.onrender.com
"""

import requests
import json
import sys

API_URL = 'https://mtg-nlp-search.onrender.com'

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f'{API_URL}/health-check', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Health check - Status: {response.status_code}')
            print(f'   Server: {data.get("status", "unknown")}')
            return True
        else:
            print(f'❌ Health check - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Health check - Error: {e}')
        return False

def test_docs_endpoint():
    """Test the API documentation endpoint"""
    try:
        response = requests.get(f'{API_URL}/docs', timeout=10)
        if response.status_code == 200:
            print(f'✅ API documentation - Status: {response.status_code}')
            return True
        else:
            print(f'❌ API documentation - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ API documentation - Error: {e}')
        return False

def test_search_endpoint():
    """Test the search endpoint with a basic query"""
    try:
        params = {'prompt': 'counterspell', 'page': 1, 'per_page': 5}
        response = requests.get(f'{API_URL}/search', params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and isinstance(data['results'], list):
                results_count = len(data['results'])
                print(f'✅ Search endpoint - Found {results_count} results')
                
                # Validate response structure
                required_fields = ['results', 'filters', 'scryfall_query', 'pagination']
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f'⚠️  Missing response fields: {missing_fields}')
                    return False
                
                return True
            else:
                print('❌ Search endpoint - Invalid response structure')
                return False
        else:
            print(f'❌ Search endpoint - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Search endpoint - Error: {e}')
        return False

def run_all_tests():
    """Run all deployed API tests"""
    print("🧪 MTG NLP Search - Deployed API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("API Documentation", test_docs_endpoint),
        ("Search Functionality", test_search_endpoint)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 DEPLOYED API TESTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 ALL DEPLOYED API TESTS PASSED!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
