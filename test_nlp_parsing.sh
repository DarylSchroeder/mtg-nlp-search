#!/bin/bash

# NLP Parsing Tests - Tests the filter extraction logic directly
# This tests the core parsing without needing the full API

cd mtg-nlp-search

PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== NLP Parsing Tests ==="
echo ""

# Test counter effect detection
test_counter_effect() {
    local test_name="$1"
    local query="$2"
    local should_have_counter="$3"  # true or false
    
    echo -n "Testing: $test_name... "
    
    # Run the NLP parser
    result=$(python3 -c "
from app.nlp import extract_filters
result = extract_filters('$query')
effects = result.get('effects', [])
has_counter = 'counter' in effects
print('true' if has_counter else 'false')
")
    
    if [ "$result" = "$should_have_counter" ]; then
        echo -e "${GREEN}PASS${NC} - Counter effect: $result"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - Expected: $should_have_counter, Got: $result"
        ((FAILED++))
    fi
}

# Test mana cost extraction
test_mana_cost() {
    local test_name="$1"
    local query="$2"
    local expected_cmc="$3"
    
    echo -n "Testing: $test_name... "
    
    result=$(python3 -c "
from app.nlp import extract_filters
result = extract_filters('$query')
cmc = result.get('cmc', 'none')
print(cmc)
")
    
    if [ "$result" = "$expected_cmc" ]; then
        echo -e "${GREEN}PASS${NC} - CMC: $result"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC} - Expected: $expected_cmc, Got: $result"
        ((FAILED++))
    fi
}

echo "Testing counter effect detection (the critical bug)..."
echo ""

# Critical tests for the "cannot be countered" bug
test_counter_effect "Abrupt Decay should NOT be counterspell" "abrupt decay" "false"
test_counter_effect "Cannot be countered should NOT be counterspell" "this spell cannot be countered" "false"
test_counter_effect "Can't be countered should NOT be counterspell" "this spell cannot be countered" "false"
test_counter_effect "Cards that cannot be countered should NOT be counterspell" "cards that cannot be countered" "false"

# Positive tests - these SHOULD be detected as counterspells
test_counter_effect "Counterspell should BE counterspell" "counterspell" "true"
test_counter_effect "1 mana counterspell should BE counterspell" "1 mana counterspell" "true"
test_counter_effect "Blue counterspell should BE counterspell" "blue counterspell" "true"

echo ""
echo "Testing mana cost extraction..."
echo ""

test_mana_cost "1 mana spell" "1 mana counterspell" "1"
test_mana_cost "2 mana creature" "2 mana creature" "2"
test_mana_cost "Zero mana spell" "0 mana artifact" "0"
test_mana_cost "No mana mentioned" "blue counterspell" "none"

echo ""
echo "=== NLP Test Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All NLP parsing tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some NLP parsing tests failed.${NC}"
    exit 1
fi
