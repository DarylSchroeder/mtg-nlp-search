#!/usr/bin/env python3
"""
Debug script to compare local vs deployed API behavior
"""

import requests
import json
from app.nlp import extract_filters
from app.scryfall import search_scryfall

def test_local_nlp():
    """Test the local NLP parser directly"""
    print("=== LOCAL NLP PARSER TEST ===")
    filters = extract_filters('2 cmc rakdos instant')
    print(f"Filters: {filters}")
    
    search_result = search_scryfall(filters)
    print(f"Scryfall Query: {search_result['query']}")
    print(f"Cards Found: {len(search_result['cards'])}")
    
    if search_result['cards']:
        first = search_result['cards'][0]
        print(f"First Result: {first['name']} - {first['mana_cost']}")
    
    return filters, search_result

def test_local_api():
    """Test the local API endpoint"""
    print("\n=== LOCAL API ENDPOINT TEST ===")
    try:
        response = requests.get("http://localhost:8000/search", 
                              params={"prompt": "2 cmc rakdos instant"})
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Filters: {data.get('filters', 'MISSING')}")
        print(f"Scryfall Query: {data.get('scryfall_query', 'MISSING')}")
        print(f"Results: {len(data.get('results', []))}")
        
        if data.get('results'):
            first = data['results'][0]
            print(f"First Result: {first['name']} - {first['mana_cost']}")
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_deployed_api():
    """Test the deployed API endpoint"""
    print("\n=== DEPLOYED API ENDPOINT TEST ===")
    try:
        response = requests.get("https://mtg-nlp-search.onrender.com/search", 
                              params={"prompt": "2 cmc rakdos instant"})
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Filters: {data.get('filters', 'MISSING')}")
        print(f"Scryfall Query: {data.get('scryfall_query', 'MISSING')}")
        print(f"Results: {len(data.get('results', []))}")
        
        if data.get('results'):
            first = data['results'][0]
            print(f"First Result: {first['name']} - {first['mana_cost']}")
            
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

def compare_results(local_nlp, local_api, deployed_api):
    """Compare all three results"""
    print("\n=== COMPARISON ANALYSIS ===")
    
    if local_nlp and local_api and deployed_api:
        local_nlp_filters, local_nlp_search = local_nlp
        
        print(f"Local NLP Filters:     {local_nlp_filters}")
        print(f"Local API Filters:     {local_api.get('filters', 'MISSING')}")
        print(f"Deployed API Filters:  {deployed_api.get('filters', 'MISSING')}")
        
        print(f"\nLocal NLP Query:       {local_nlp_search['query']}")
        print(f"Local API Query:       {local_api.get('scryfall_query', 'MISSING')}")
        print(f"Deployed API Query:    {deployed_api.get('scryfall_query', 'MISSING')}")
        
        print(f"\nLocal NLP Results:     {len(local_nlp_search['cards'])}")
        print(f"Local API Results:     {len(local_api.get('results', []))}")
        print(f"Deployed API Results:  {len(deployed_api.get('results', []))}")
        
        # Check for the regression
        if deployed_api.get('results'):
            first_deployed = deployed_api['results'][0]
            if first_deployed['mana_cost'] == '{1}{W}':
                print(f"\n🚨 REGRESSION CONFIRMED: Deployed API returns 1-mana white card!")
                print(f"   First result: {first_deployed['name']} - {first_deployed['mana_cost']}")
            else:
                print(f"\n✅ Deployed API looks correct")
                print(f"   First result: {first_deployed['name']} - {first_deployed['mana_cost']}")

if __name__ == "__main__":
    print("🧪 MTG API Deployment Debug Script")
    print("=" * 50)
    
    # Test all three approaches
    local_nlp_result = test_local_nlp()
    local_api_result = test_local_api()
    deployed_api_result = test_deployed_api()
    
    # Compare results
    compare_results(local_nlp_result, local_api_result, deployed_api_result)
    
    print("\n" + "=" * 50)
    print("Debug complete!")
