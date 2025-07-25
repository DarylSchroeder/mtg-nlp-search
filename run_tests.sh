#!/bin/bash

# Simple test runner for MTG NLP Search
# No frameworks, just basic bash and curl

API_URL="http://localhost:8000/search"
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== MTG NLP Search Tests ==="
echo ""

# Helper function to test a query
test_query() {
    local test_name="$1"
    local query="$2"
    local expected_behavior="$3"
    
    echo -n "Testing: $test_name... "
    
    # Make the API call
    response=$(curl -s -G "$API_URL" --data-urlencode "prompt=$query")
    
    # Check if we got a valid JSON response
    if ! echo "$response" | grep -q '"prompt"'; then
        echo -e "${RED}FAIL${NC} - Invalid response"
        ((FAILED++))
        return
    fi
    
    # Count results
    result_count=$(echo "$response" | grep -o '"name":"[^"]*"' | wc -l)
    
    # Basic success check - got some results
    if [ "$result_count" -gt 0 ]; then
        echo -e "${GREEN}PASS${NC} - Found $result_count results"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - No results found"
        ((FAILED++))
    fi
}

# Test that should find no results
test_no_results() {
    local test_name="$1"
    local query="$2"
    
    echo -n "Testing: $test_name... "
    
    response=$(curl -s -G "$API_URL" --data-urlencode "prompt=$query")
    result_count=$(echo "$response" | grep -o '"name":"[^"]*"' | wc -l)
    
    if [ "$result_count" -eq 0 ]; then
        echo -e "${GREEN}PASS${NC} - Correctly found no results"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - Found $result_count results (expected 0)"
        ((FAILED++))
    fi
}

# Test specific card inclusion
test_includes_card() {
    local test_name="$1"
    local query="$2"
    local expected_card="$3"
    
    echo -n "Testing: $test_name... "
    
    response=$(curl -s -G "$API_URL" --data-urlencode "prompt=$query")
    
    if echo "$response" | grep -q "\"name\":\"$expected_card\""; then
        echo -e "${GREEN}PASS${NC} - Found '$expected_card'"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - '$expected_card' not found"
        ((FAILED++))
    fi
}

# Test specific card exclusion
test_excludes_card() {
    local test_name="$1"
    local query="$2"
    local excluded_card="$3"
    
    echo -n "Testing: $test_name... "
    
    response=$(curl -s -G "$API_URL" --data-urlencode "prompt=$query")
    
    if ! echo "$response" | grep -q "\"name\":\"$excluded_card\""; then
        echo -e "${GREEN}PASS${NC} - Correctly excluded '$excluded_card'"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - '$excluded_card' should not appear"
        ((FAILED++))
    fi
}

echo "Running basic functionality tests..."
echo ""

# Basic mana cost tests
test_query "1 mana counterspell" "1 mana counterspell" "Should find 1-cost counterspells"
test_query "2 mana instant" "2 mana instant" "Should find 2-cost instants"
test_query "3 mana creature" "3 mana creature" "Should find 3-cost creatures"

# Color identity tests
test_query "azorius counterspell" "azorius counterspell" "Should find white/blue counterspells"
test_query "simic ramp" "simic ramp" "Should find green/blue ramp spells"

# Commander deck tests
test_query "counterspell for Chulane deck" "counterspell that will fit in my Chulane deck" "Should find GWU counterspells"

# Land type tests
test_query "fetchland" "fetchland" "Should find fetch lands"
test_query "shockland" "shockland" "Should find shock lands"

# Specific inclusion tests
test_includes_card "1-mana counterspell includes Abjure" "1 mana counterspell" "Abjure"
test_includes_card "Fetchlands include Polluted Delta" "fetchland" "Polluted Delta"

# Specific exclusion tests (our new critical tests)
test_excludes_card "Chulane counterspells exclude Leyline of Lifeforce" "counterspell that will fit in my Chulane deck" "Leyline of Lifeforce"

echo ""
echo "=== Test Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
