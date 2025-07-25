#!/usr/bin/env python3
"""
Direct API test to verify the exact behavior and response format
"""

import requests
import json
import sys

def test_api_call(query):
    """Test the MTG NLP Search API directly"""
    
    print(f"🔍 Testing query: '{query}'")
    print("=" * 50)
    
    # API endpoint
    url = "https://mtg-nlp-search.onrender.com/search"
    
    # Parameters
    params = {
        'prompt': query,
        'page': 1,
        'per_page': 3  # Small number for testing
    }
    
    try:
        print("📡 Making API request...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n🎯 API Response Analysis:")
            print("-" * 30)
            
            # Check what fields are present
            print("📋 Available fields:")
            for key in data.keys():
                print(f"  ✅ {key}: {type(data[key])}")
            
            print(f"\n🔤 Prompt: {data.get('prompt', 'MISSING')}")
            
            # Check filters
            filters = data.get('filters')
            if filters:
                print(f"🎛️  Filters: {json.dumps(filters, indent=2)}")
            else:
                print("❌ No 'filters' field found")
            
            # Check for parsed_filters (old field name)
            parsed_filters = data.get('parsed_filters')
            if parsed_filters:
                print(f"🎛️  Parsed Filters: {json.dumps(parsed_filters, indent=2)}")
            else:
                print("❌ No 'parsed_filters' field found")
            
            # Check scryfall_query
            scryfall_query = data.get('scryfall_query')
            if scryfall_query:
                print(f"🔍 Scryfall Query: '{scryfall_query}'")
            else:
                print("❌ No 'scryfall_query' field found")
            
            # Check results
            results = data.get('results', [])
            print(f"\n📦 Results: {len(results)} cards found")
            
            if results:
                print("🃏 First few cards:")
                for i, card in enumerate(results[:3]):
                    name = card.get('name', 'Unknown')
                    mana_cost = card.get('mana_cost', 'N/A')
                    type_line = card.get('type_line', 'N/A')
                    colors = card.get('colors', [])
                    color_identity = card.get('color_identity', [])
                    
                    print(f"  {i+1}. {name}")
                    print(f"     Cost: {mana_cost}")
                    print(f"     Type: {type_line}")
                    print(f"     Colors: {colors}")
                    print(f"     Color Identity: {color_identity}")
                    print()
            
            # Pagination info
            pagination = data.get('pagination', {})
            if pagination:
                print(f"📄 Pagination:")
                print(f"  Page: {pagination.get('page')}/{pagination.get('total_pages')}")
                print(f"  Total Results: {pagination.get('total_results')}")
            
            print("\n" + "=" * 50)
            print("✅ API TEST COMPLETE")
            
            return data
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_frontend_processing(api_data, query):
    """Test how the frontend would process this data"""
    
    print(f"\n🖥️  Frontend Processing Test")
    print("=" * 50)
    
    if not api_data:
        print("❌ No API data to process")
        return
    
    # Simulate what the frontend does
    frontend_data = {
        'timestamp': '2025-07-25T18:00:00.000Z',
        'searchQuery': query,
        'apiUrl': f'https://mtg-nlp-search.onrender.com/search?prompt={query}&page=1&per_page=3',
        'responseData': api_data,
        'scryfallQuery': api_data.get('scryfall_query') or None,
        'parsedFilters': api_data.get('filters') or None  # This is the key fix
    }
    
    print("🔧 Frontend would create this lastScryfallCall object:")
    print(json.dumps(frontend_data, indent=2))
    
    # Check if bug report would work
    print(f"\n📋 Bug Report Fields:")
    print(f"  ✅ parsedFilters: {frontend_data['parsedFilters'] is not None}")
    print(f"  ✅ scryfallQuery: {frontend_data['scryfallQuery'] is not None}")
    
    if frontend_data['parsedFilters'] is None:
        print("❌ BUG: parsedFilters would be null in bug report!")
    
    if frontend_data['scryfallQuery'] is None:
        print("❌ BUG: scryfallQuery would be 'N/A' in bug report!")
    
    return frontend_data

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "1 cmc white artifact",
        "counterspell",
        "fetchland",
        "invalid query xyz123"
    ]
    
    if len(sys.argv) > 1:
        test_queries = [sys.argv[1]]
    
    for query in test_queries:
        api_data = test_api_call(query)
        frontend_data = test_frontend_processing(api_data, query)
        print("\n" + "🔄" * 25 + "\n")
