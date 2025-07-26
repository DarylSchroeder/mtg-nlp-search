#!/usr/bin/env python3
"""
Test script to validate the deployment is working
"""
import requests
import json
import time

def test_deployment():
    base_url = "https://mtg-nlp-search.onrender.com"
    
    print("🧪 Testing Deployment:")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health-check", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK")
            print(f"   Status: {data.get('status')}")
            print(f"   Git branch: {data.get('deployment', {}).get('git_branch')}")
            print(f"   Git commit: {data.get('deployment', {}).get('git_commit')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Critical query
    print("\n2. Testing critical query...")
    try:
        response = requests.get(
            f"{base_url}/search", 
            params={"prompt": "adds +1/+1 counters"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            query = data.get('scryfall_query', '')
            if 'o:"+1/+1 counter"' in query:
                print("✅ Critical bug fix working!")
                print(f"   Query: {query}")
            else:
                print("❌ Critical bug fix not working")
                print(f"   Query: {query}")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    print("\n🎯 Deployment test complete!")

if __name__ == "__main__":
    test_deployment()
