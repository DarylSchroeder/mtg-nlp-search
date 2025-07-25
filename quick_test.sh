#!/bin/bash

API_URL="http://localhost:8000/search"

echo "=== Quick Test Results ==="

test_queries=(
    "12/12 dinosaur"
    "shockland" 
    "rakdos removal spell"
    "azorius counterspell"
    "fetchland"
    "2 mana instant that draws cards"
    "counterspell that will fit in my Chulane deck"
    "commander"
    "vanilla creature"
    "split card"
)

success_count=0
total_count=${#test_queries[@]}

for query in "${test_queries[@]}"; do
    echo "Testing: \"$query\""
    
    response=$(curl -s -G "$API_URL" --data-urlencode "prompt=$query")
    
    if echo "$response" | grep -q '"results":\[{'; then
        echo "✅ SUCCESS"
        first_card=$(echo "$response" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo "   First result: $first_card"
        ((success_count++))
    else
        echo "❌ FAILED"
    fi
    echo ""
done

echo "=== SUMMARY ==="
echo "Success Rate: $success_count/$total_count ($(( success_count * 100 / total_count ))%)"
