# MTG NLP Search - Testing Guide

## Test Suites

### 1. Basic Functionality Tests
```bash
./run_tests.sh
```
Tests core search functionality with simple queries.

### 2. Color vs Color Identity Tests
```bash
python3 test_color_vs_identity.py
```
Comprehensive test suite that validates the critical distinction between `color:` and `coloridentity:` in Scryfall queries.

## Color vs Color Identity Logic

### ✅ **Positive Cases** - Should use `color:` (actual card color)
These queries search for cards that are actually the specified color:

| Query | Expected Filter | Expected Query | Description |
|-------|----------------|----------------|-------------|
| `"1 cmc white artifact"` | `colors: "W"` | `color:W` | White artifacts that cost 1 mana |
| `"blue creature 3 mana"` | `colors: "U"` | `color:U` | Blue creatures that cost 3 mana |
| `"red instant 2 cmc"` | `colors: "R"` | `color:R` | Red instants that cost 2 mana |
| `"green sorcery"` | `colors: "G"` | `color:G` | Green sorcery spells |
| `"black enchantment"` | `colors: "B"` | `color:B` | Black enchantments |

### ❌ **Negative Cases** - Should use `coloridentity:` (Commander deck building)
These queries are for Commander deck building and use color identity:

| Query | Expected Filter | Expected Query | Description |
|-------|----------------|----------------|-------------|
| `"azorius counterspell"` | `coloridentity: "WU"` | `coloridentity:WU` | Counterspells legal in W/U decks |
| `"simic ramp"` | `coloridentity: "GU"` | `coloridentity:GU` | Ramp spells legal in G/U decks |
| `"counterspell for my Chulane deck"` | `coloridentity: "GWU"` | `coloridentity:GWU` | Counterspells for Bant commander |
| `"removal for Atraxa"` | `coloridentity: "WUBG"` | `coloridentity:WUBG` | Removal for 4-color commander |
| `"white fetchland"` | Direct query | `coloridentity:W` | Fetchlands for white decks |
| `"blue shockland"` | Direct query | `coloridentity:U` | Shocklands for blue decks |
| `"white commander"` | Direct query | `coloridentity:W` | White commanders |

### 🎯 **Key Distinctions**

1. **Card Types**: `artifact`, `creature`, `instant`, `sorcery`, `enchantment`, `planeswalker` → Use `color:`
2. **Guild Names**: `azorius`, `simic`, `rakdos`, etc. → Use `coloridentity:`
3. **Commander Context**: `"for my X deck"`, `"X commander"` → Use `coloridentity:`
4. **Land Types**: `fetchland`, `shockland`, `triome` → Use `coloridentity:`

### 🔧 **Color Order (WUBRG)**
Magic uses canonical WUBRG color order:
- ✅ `simic` → `GU` (Green-Blue)
- ❌ `simic` → `UG` (incorrect order)

## Test Results Validation

### Expected Test Output
```
🧪 MTG NLP Search - Color vs Color Identity Test Suite
============================================================
📊 TEST RESULTS: 13 passed, 0 failed
🎉 ALL TESTS PASSED! Color vs Color Identity logic is working correctly.
```

### Debugging Failed Tests
If tests fail, check:

1. **Color Order**: Ensure guilds use WUBRG order (`simic` = `GU`, not `UG`)
2. **Filter Types**: Direct queries use `scryfall_query` field, not individual filters
3. **API Deployment**: Local changes need to be deployed to test against live API

## Running Individual Tests

### Test Specific Query Types
```bash
# Test guild names
python3 -c "
from app.nlp import extract_filters
print('Azorius:', extract_filters('azorius counterspell'))
print('Simic:', extract_filters('simic ramp'))
"

# Test commander queries  
python3 -c "
from app.nlp import extract_filters
print('Commander:', extract_filters('white commander'))
print('Deck context:', extract_filters('removal for Atraxa'))
"

# Test land types
python3 -c "
from app.nlp import extract_filters
print('Fetchland:', extract_filters('white fetchland'))
print('Shockland:', extract_filters('blue shockland'))
"
```

### Test Color vs Identity Logic
```bash
# Should use color: (actual card color)
python3 -c "
from app.nlp import extract_filters
print('Artifact:', extract_filters('1 cmc white artifact'))
print('Creature:', extract_filters('blue creature 3 mana'))
"

# Should use coloridentity: (deck building)
python3 -c "
from app.nlp import extract_filters  
print('Guild:', extract_filters('azorius counterspell'))
print('Commander:', extract_filters('removal for Atraxa'))
"
```

## Continuous Integration

Add to your CI pipeline:
```yaml
- name: Run Color vs Identity Tests
  run: python3 test_color_vs_identity.py
  
- name: Validate Test Results
  run: |
    if python3 test_color_vs_identity.py | grep -q "ALL TESTS PASSED"; then
      echo "✅ Color vs Identity logic is working correctly"
    else
      echo "❌ Color vs Identity tests failed"
      exit 1
    fi
```

## Performance Testing

The test suite includes rate limiting (`time.sleep(1)`) to avoid overwhelming the API. For faster testing during development, you can reduce or remove the delays.

## Edge Cases Covered

1. **Multicolor without specific colors**: `"multicolor artifact"` → No color filter
2. **Commander with colors**: `"white commander"` → `coloridentity:W`
3. **Land types with colors**: `"white fetchland"` → `coloridentity:W`
4. **Guild names**: All 10 guilds + 5 shards + 5 wedges
5. **Famous commanders**: Chulane, Atraxa, Alesha, etc.

This comprehensive testing ensures the NLP parser correctly distinguishes between actual card colors and Commander deck building contexts.
