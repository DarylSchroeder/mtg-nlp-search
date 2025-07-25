#!/usr/bin/env python3
"""
Integration tests for API functionality
Consolidated from: run_tests.sh, quick_test.sh, test_api_direct.py, test_scenarios.sh
"""

import requests
import json
import sys
import time

API_BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        
    def test_health_endpoint(self):
        """Test health check endpoint"""
        print("🏥 Testing health endpoint...")
        
        try:
            response = requests.get(f"{API_BASE_URL}/health-check", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            required_fields = ["status", "timestamp", "uptime", "deployment"]
            
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            assert data["status"] == "healthy"
            print("✅ PASS: Health endpoint working")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ FAIL: Health endpoint - {e}")
            self.failed += 1
    
    def test_search_query(self, query, expected_behavior="should return results"):
        """Test a search query"""
        print(f"🔍 Testing: '{query}'...")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/search", 
                params={"prompt": query},
                timeout=10
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Validate response structure
            required_fields = ["prompt", "filters", "scryfall_query", "results", "pagination"]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            result_count = len(data["results"])
            
            if "should return results" in expected_behavior:
                assert result_count > 0, f"Expected results but got {result_count}"
                print(f"✅ PASS: '{query}' -> {result_count} results")
            elif "should return no results" in expected_behavior:
                assert result_count == 0, f"Expected no results but got {result_count}"
                print(f"✅ PASS: '{query}' -> correctly no results")
            else:
                print(f"✅ PASS: '{query}' -> {result_count} results")
            
            self.passed += 1
            return data
            
        except Exception as e:
            print(f"❌ FAIL: '{query}' - {e}")
            self.failed += 1
            return None
    
    def test_card_inclusion(self, query, expected_card):
        """Test that a specific card appears in results"""
        print(f"🎯 Testing: '{query}' includes '{expected_card}'...")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"prompt": query},
                timeout=10
            )
            
            assert response.status_code == 200
            data = response.json()
            
            card_names = [card["name"] for card in data["results"]]
            assert expected_card in card_names, f"'{expected_card}' not found in results"
            
            print(f"✅ PASS: '{query}' includes '{expected_card}'")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ FAIL: '{query}' should include '{expected_card}' - {e}")
            self.failed += 1
    
    def test_card_exclusion(self, query, excluded_card):
        """Test that a specific card does NOT appear in results"""
        print(f"🚫 Testing: '{query}' excludes '{excluded_card}'...")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"prompt": query}, 
                timeout=10
            )
            
            assert response.status_code == 200
            data = response.json()
            
            card_names = [card["name"] for card in data["results"]]
            assert excluded_card not in card_names, f"'{excluded_card}' should not appear"
            
            print(f"✅ PASS: '{query}' correctly excludes '{excluded_card}'")
            self.passed += 1
            
        except Exception as e:
            print(f"❌ FAIL: '{query}' should exclude '{excluded_card}' - {e}")
            self.failed += 1

def run_comprehensive_tests():
    """Run all integration tests"""
    tester = APITester()
    
    print("🌐 Running API Integration Tests...")
    print("=" * 60)
    
    # Health check
    tester.test_health_endpoint()
    print()
    
    # Basic functionality tests
    print("📋 Basic Functionality Tests:")
    basic_tests = [
        ("1 mana counterspell", "should return results"),
        ("fetchland", "should return results"), 
        ("shockland", "should return results"),
        ("2 mana instant", "should return results"),
        ("3 mana creature", "should return results")
    ]
    
    for query, behavior in basic_tests:
        tester.test_search_query(query, behavior)
    print()
    
    # Guild and commander tests
    print("🏛️ Guild & Commander Tests:")
    guild_tests = [
        ("azorius counterspell", "should return results"),
        ("simic ramp", "should return results"),
        ("counterspell for Chulane deck", "should return results")
    ]
    
    for query, behavior in guild_tests:
        tester.test_search_query(query, behavior)
    print()
    
    # Specific card inclusion tests
    print("🎯 Card Inclusion Tests:")
    inclusion_tests = [
        ("1 mana counterspell", "Abjure"),
        ("fetchland", "Polluted Delta"),
        ("shockland", "Blood Crypt")
    ]
    
    for query, card in inclusion_tests:
        tester.test_card_inclusion(query, card)
    print()
    
    # Critical exclusion tests (the bug we fixed)
    print("🚫 Critical Exclusion Tests:")
    exclusion_tests = [
        ("counterspell", "Abrupt Decay"),
        ("1 mana counterspell", "Abrupt Decay"),
        ("counterspell for Chulane deck", "Leyline of Lifeforce")
    ]
    
    for query, card in exclusion_tests:
        tester.test_card_exclusion(query, card)
    print()
    
    # Edge cases
    print("🔬 Edge Case Tests:")
    edge_tests = [
        ("invalid query xyz123", "should return no results"),
        ("", "should return no results")
    ]
    
    for query, behavior in edge_tests:
        tester.test_search_query(query, behavior)
    
    print("=" * 60)
    print(f"📊 Test Results: {tester.passed} passed, {tester.failed} failed")
    
    if tester.failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed.")
        return False

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health-check", timeout=2)
        if response.status_code != 200:
            raise Exception("Server not healthy")
    except:
        print("❌ Server not running at http://localhost:8000")
        print("Please start the server first:")
        print("cd backend/mtg-nlp-search && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
