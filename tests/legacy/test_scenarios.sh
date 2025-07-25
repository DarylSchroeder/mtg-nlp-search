#!/bin/bash

# Test all 50 scenarios
API_URL="http://localhost:8000/search"

echo "=== MTG NLP Search Test Results ==="
echo "Testing 50 scenarios..."
echo ""

# Function to test a query
test_query() {
    local num=$1
    local query=$2
    local expected=$3
    
    echo "Test $num: \"$query\""
    echo "Expected: $expected"
    
    response=$(curl -s -G "$API_URL" \
        --data-urlencode "prompt=$query")
    
    # Check if response contains error
    if echo "$response" | grep -q '"error"'; then
        echo "❌ ERROR: $(echo "$response" | grep -o '"error":"[^"]*"')"
    elif echo "$response" | grep -q '"results"'; then
        result_count=$(echo "$response" | grep -o '"results":\[[^]]*\]' | grep -o '{"' | wc -l)
        if [ "$result_count" -gt 0 ]; then
            echo "✅ SUCCESS: Found $result_count cards"
            # Show first card name if available
            first_card=$(echo "$response" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
            if [ ! -z "$first_card" ]; then
                echo "   First result: $first_card"
            fi
        else
            echo "⚠️  NO RESULTS: Query parsed but no cards found"
        fi
    else
        echo "❌ INVALID RESPONSE: $response"
    fi
    echo ""
}

# Power/Toughness Searches
test_query 1 "12/12 dinosaur" "Ghalta, Primal Hunger"
test_query 2 "1/1 creature that makes tokens" "Monastery Mentor"
test_query 3 "0/1 defender" "Wall of Omens"
test_query 4 "20/20 creature" "Marit Lage token creators"

# Mana Cost & Efficiency
test_query 5 "zero mana artifact that makes mana" "Black Lotus, Mox cards"
test_query 6 "1 mana counterspell" "Spell Pierce, Mental Misstep"
test_query 7 "2 mana instant that draws cards" "Divination, Think Twice"
test_query 8 "3 mana planeswalker" "3-cost planeswalkers"

# Guild Names
test_query 9 "rakdos removal spell" "Terminate, Dreadbore"
test_query 10 "azorius counterspell" "Dovin's Veto, Absorb"
test_query 11 "golgari creature" "BG creatures"
test_query 12 "simic card draw" "Urban Evolution, Kruphix"
test_query 13 "boros aggro creature" "RW aggressive creatures"

# Shard Names
test_query 14 "esper control spell" "WUB control spells"
test_query 15 "naya creature" "RGW creatures"
test_query 16 "jund removal" "BRG removal"

# Wedge Names
test_query 17 "abzan creature" "WBG creatures"
test_query 18 "jeskai instant" "URW instants"
test_query 19 "sultai card" "UBG cards"

# Commander Color Identity
test_query 20 "counterspell that will fit in my Chulane deck" "GWU counterspells"
test_query 21 "removal spell for my Alesha deck" "RWB removal"
test_query 22 "ramp spell for my Kenrith deck" "5-color ramp"

# Land Vernacular (Very Common)
test_query 23 "shockland" "Blood Crypt, Steam Vents"
test_query 24 "fetchland" "Polluted Delta, Windswept Heath"
test_query 25 "triome" "Indatha Triome, Ketria Triome"
test_query 26 "checkland" "Dragonskull Summit, Glacial Fortress"
test_query 27 "fastland" "Blackcleave Cliffs, Seachrome Coast"

# Land Vernacular (Moderately Common)
test_query 28 "painland" "Caves of Koilos, Llanowar Wastes"
test_query 29 "filterland" "Mystic Gate, Sunken Ruins"
test_query 30 "bounceland" "Azorius Chancery, Dimir Aqueduct"
test_query 31 "scryland" "Temple of Enlightenment, Temple of Malice"
test_query 32 "creatureland" "Celestial Colonnade, Raging Ravine"

# Card Type Vernacular
test_query 33 "commander" "legendary creatures"
test_query 34 "vanilla creature" "creatures with no abilities"
test_query 35 "french vanilla creature" "creatures with only keyword abilities"

# Mechanic Vernacular
test_query 36 "double-faced card" "Delver of Secrets, Huntmaster"
test_query 37 "modal double-faced card" "Zendikar Rising DFCs"
test_query 38 "split card" "Fire // Ice, Life // Death"
test_query 39 "transform card" "Innistrad transform cards"

# Combined Vernacular + Color Identity
test_query 40 "rakdos shockland" "Blood Crypt"
test_query 41 "simic fetchland" "Misty Rainforest"
test_query 42 "esper triome" "none exist"
test_query 43 "azorius checkland" "Glacial Fortress"
test_query 44 "golgari painland" "Llanowar Wastes"

# Combined Vernacular + Function
test_query 45 "blue fetchland" "Flooded Strand, Polluted Delta"
test_query 46 "white commander" "white legendary creatures"
test_query 47 "green vanilla creature" "green creatures with no abilities"
test_query 48 "red split card" "red split cards"

# Complex Combined Searches
test_query 49 "2 mana simic commander" "Ezuri, Cephalid Constable"
test_query 50 "jeskai instant that counters spells" "Dovin's Veto"

# Specific Edge Cases
test_query 51 "counterspell that will fit in my Chulane deck" "Should include Lifeforce (green counterspell), blue/white counterspells"
test_query 52 "counterspell that will fit in my Chulane deck" "Should NOT include Leyline of Lifeforce (prevents countering, not a counterspell)"

echo "=== Test Complete (52 scenarios) ==="
