# MTG NLP Search - CMC Parsing Fix

## Issue Report Summary
**Date**: 2025-07-25  
**Query**: "removal for Atraxa 1 cmc", "removal for Atraxa 2 cmc", "removal for Atraxa 3 cmc"  
**Problem**: All queries returned the same results - CMC filtering was not working  
**Expected**: Different results based on CMC values (1, 2, 3)  

## Root Cause
The NLP parser in `/mtg-nlp-search/app/nlp.py` was missing a regex pattern to handle "X cmc" format queries. The existing patterns were:

```python
mana_patterns = [
    r'(\d+)\s+mana',      # "1 mana"
    r'cmc\s*:?\s*(\d+)',  # "cmc 1" or "cmc: 1"  
    r'costs?\s+(\d+)',    # "cost 1" or "costs 1"
    r'(\d+)\s+cost'       # "1 cost"
]
```

But none matched "1 cmc", "2 cmc", etc.

## Solution
Added the missing regex pattern to handle "X cmc" format:

```python
mana_patterns = [
    r'(\d+)\s+mana',
    r'cmc\s*:?\s*(\d+)',
    r'(\d+)\s+cmc',       # ← NEW: Added pattern for "1 cmc", "2 cmc", etc.
    r'costs?\s+(\d+)',
    r'(\d+)\s+cost'
]
```

## Verification
Tested the fix with multiple queries:

- ✅ "removal for Atraxa 1 cmc" → `{"cmc":1,"coloridentity":"WUBG","effects":["removal"]}`
- ✅ "removal for Atraxa 2 cmc" → `{"cmc":2,"coloridentity":"WUBG","effects":["removal"]}`  
- ✅ "removal for Atraxa 3 cmc" → `{"cmc":3,"coloridentity":"WUBG","effects":["removal"]}`
- ✅ Existing patterns still work: "1 mana counterspell", "cmc 2 creatures", "3 cost artifacts"

## Files Modified
- `/mtg-nlp-search/app/nlp.py` - Added `r'(\d+)\s+cmc'` pattern to `mana_patterns` list

## Status
✅ **FIXED** - CMC filtering now works correctly for all supported formats including "X cmc"
