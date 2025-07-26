#!/usr/bin/env python3
"""
Unit tests for QueryBuilder - carries over all existing test cases from test_nlp.py
Plus additional tests for the builder pattern approach
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../mtg-nlp-search'))

from app.query_builder import extract_filters, QueryBuilder


class TestQueryBuilder:
    """Test suite for QueryBuilder functionality"""
    
    def test_counter_effect_detection(self):
        """Test that counter effect detection works correctly (critical bug fix)"""
        
        # These should NOT be detected as counterspells
        negative_cases = [
            "Abrupt Decay",
            "Cannot be countered", 
            "Can't be countered",
            "Cards that cannot be countered",
            "adds +1/+1 counters",  # NEW: This was the problematic case
            "put a +1/+1 counter"
        ]
        
        for query in negative_cases:
            result = extract_filters(query)
            scryfall_query = result.get("scryfall_query", "")
            
            # Should not contain counterspell oracle text
            assert 'o:"counter target"' not in scryfall_query, f"'{query}' should NOT be counterspell"
            print(f"✅ PASS: '{query}' correctly NOT detected as counterspell")
        
        # These SHOULD be detected as counterspells
        positive_cases = [
            "counterspell",
            "1 mana counterspell", 
            "blue counterspell",
            "counter target spell"
        ]
        
        for query in positive_cases:
            result = extract_filters(query)
            scryfall_query = result.get("scryfall_query", "")
            
            # Should contain counterspell oracle text
            assert 'o:"counter target"' in scryfall_query, f"'{query}' should BE counterspell"
            print(f"✅ PASS: '{query}' correctly detected as counterspell")
    
    def test_mana_cost_extraction(self):
        """Test mana cost parsing"""
        
        test_cases = [
            ("1 mana spell", 1),
            ("2 mana creature", 2), 
            ("3 cost artifact", 3),
            ("4 cmc instant", 4),
            ("zero mana spell", 0),
            ("x cost spell", None),  # X cost handled specially
            ("no mana mentioned", None)
        ]
        
        for query, expected_cmc in test_cases:
            result = extract_filters(query)
            actual_cmc = result.get("cmc")
            
            if expected_cmc is None:
                # X cost should create special scryfall query
                if "x cost" in query:
                    assert "mana>=X" in result.get("scryfall_query", ""), f"'{query}' should handle X cost"
                else:
                    assert actual_cmc is None, f"'{query}' should have no CMC"
            else:
                assert actual_cmc == expected_cmc, f"'{query}' should have CMC {expected_cmc}, got {actual_cmc}"
            
            print(f"✅ PASS: '{query}' -> CMC: {actual_cmc}")
    
    def test_color_vs_identity_logic(self):
        """Test color vs color identity distinction - CRITICAL for builder pattern"""
        
        # Individual colors should use 'colors' field
        individual_color_cases = [
            ("1 cmc white artifact", {"cmc": 1, "type": "artifact", "colors": "W"}),
            ("blue creature 3 mana", {"cmc": 3, "type": "creature", "colors": "U"}),
            ("red instant 2 cmc", {"cmc": 2, "type": "instant", "colors": "R"}),
            ("green sorcery", {"type": "sorcery", "colors": "G"}),
            ("black enchantment", {"type": "enchantment", "colors": "B"})
        ]
        
        for query, expected_filters in individual_color_cases:
            result = extract_filters(query)
            
            for key, expected_value in expected_filters.items():
                actual_value = result.get(key)
                assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
            
            # Individual colors should use 'colors', not 'coloridentity'
            assert 'colors' in result, f"'{query}' should have 'colors' field"
            assert 'coloridentity' not in result, f"'{query}' should not have 'coloridentity' field"
            
            print(f"✅ PASS: '{query}' uses 'colors' correctly")
        
        # Guild names should use 'coloridentity' field
        guild_cases = [
            ("rakdos removal", {"coloridentity": "BR"}),
            ("selesnya enchantment", {"type": "enchantment", "coloridentity": "GW"}),
            ("azorius counterspell", {"coloridentity": "WU"}),
            ("simic ramp", {"coloridentity": "GU"}),
            ("izzet draw", {"coloridentity": "UR"})
        ]
        
        for query, expected_filters in guild_cases:
            result = extract_filters(query)
            
            for key, expected_value in expected_filters.items():
                actual_value = result.get(key)
                assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
            
            # Guild names should use 'coloridentity', not 'colors'
            assert 'coloridentity' in result, f"'{query}' should have 'coloridentity' field"
            assert 'colors' not in result, f"'{query}' should not have 'colors' field"
            
            print(f"✅ PASS: '{query}' uses 'coloridentity' correctly")
        
        # Commander contexts should use 'coloridentity'
        commander_cases = [
            "counterspell for my Chulane deck",
            "removal for Atraxa",  # This was the failing case!
            "ramp for Omnath",
            "draw for Niv-Mizzet"
        ]
        
        for query in commander_cases:
            result = extract_filters(query)
            
            # Should use coloridentity
            assert "coloridentity" in result, f"'{query}' should use coloridentity"
            assert "colors" not in result, f"'{query}' should not use colors"
            
            print(f"✅ PASS: '{query}' uses coloridentity for commander context")
    
    def test_effect_modifiers(self):
        """Test effect modifiers that transform queries"""
        
        modifier_cases = [
            # Removal modifiers
            ("blue artifact removal", {
                "colors": "U",
                "scryfall_query": "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:artifact or o:permanent)"
            }),
            ("removal for Atraxa", {
                "coloridentity": "WUBG",
                "scryfall_query": "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent)"
            }),
            
            # Counterspell modifiers
            ("1 mana counterspell", {
                "cmc": 1,
                "type": "instant",
                "scryfall_query": "o:\"counter target\""
            }),
            
            # Ramp modifiers
            ("green ramp spell", {
                "colors": "G",
                "scryfall_query": "(o:\"search your library\" o:land) or (o:\"add\" o:\"mana\")"
            }),
            
            # Draw modifiers
            ("blue draw spell", {
                "colors": "U", 
                "scryfall_query": "o:\"draw\" o:\"card\""
            })
        ]
        
        for query, expected_filters in modifier_cases:
            result = extract_filters(query)
            
            for key, expected_value in expected_filters.items():
                actual_value = result.get(key)
                assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
            
            print(f"✅ PASS: '{query}' modifier applied correctly")
    
    def test_special_card_types(self):
        """Test special card type detection"""
        
        special_cases = [
            ("fetchland", "o:\"search your library\" o:\"shuffle\" type:land"),
            ("shockland", "o:\"as ~ enters\" o:\"2 damage\" type:land"),
            ("triome", "o:\"cycling\" o:\"enters tapped\" type:land"),
            ("dual land", "o:\"{\" o:\"}\" type:land"),
            ("basic land", "type:basic type:land"),
            ("utility land", "type:land -type:basic")
        ]
        
        for query, expected_scryfall in special_cases:
            result = extract_filters(query)
            
            scryfall_query = result.get("scryfall_query", "")
            assert scryfall_query == expected_scryfall, f"'{query}' should have scryfall: {expected_scryfall}, got: {scryfall_query}"
            
            print(f"✅ PASS: '{query}' detected special type correctly")
    
    def test_compound_types(self):
        """Test compound card types"""
        
        compound_cases = [
            ("artifact creature", "type:artifact type:creature"),
            ("legendary creature", "type:legendary type:creature"),
            ("tribal instant", "type:tribal type:instant"),
            ("enchantment creature", "type:enchantment type:creature")
        ]
        
        for query, expected_scryfall in compound_cases:
            result = extract_filters(query)
            
            scryfall_query = result.get("scryfall_query", "")
            assert scryfall_query == expected_scryfall, f"'{query}' should have scryfall: {expected_scryfall}, got: {scryfall_query}"
            
            print(f"✅ PASS: '{query}' compound type detected correctly")
    
    def test_pump_effects(self):
        """Test +1/+1 counter effects (the problematic case)"""
        
        pump_cases = [
            "creature with +1/+1 counters",
            "adds +1/+1 counters", 
            "put a +1/+1 counter"
        ]
        
        for query in pump_cases:
            result = extract_filters(query)
            scryfall_query = result.get("scryfall_query", "")
            
            # Should contain +1/+1 counter oracle text, NOT counterspell text
            assert 'o:"+1/+1 counter"' in scryfall_query, f"'{query}' should detect +1/+1 counters"
            assert 'o:"counter target"' not in scryfall_query, f"'{query}' should NOT be counterspell"
            
            print(f"✅ PASS: '{query}' correctly detected as +1/+1 counter effect")
    
    def test_tokenization(self):
        """Test that tokenization preserves important phrases"""
        
        builder = QueryBuilder()
        
        test_cases = [
            ("artifact creature", ["artifact creature"]),  # Should be preserved as one token
            ("card draw spell", ["card", "draw", "spell"]),  # "card draw" should be preserved
            ("+1/+1 counter", ["+1/+1 counter"]),  # Should be preserved
            ("dual land", ["dual land"]),  # Should be preserved
            ("basic land", ["basic land"])  # Should be preserved
        ]
        
        for query, expected_tokens in test_cases:
            tokens = builder._tokenize(query)
            
            # Check that important phrases are preserved
            for expected_token in expected_tokens:
                if ' ' in expected_token:  # Multi-word phrase
                    assert expected_token in tokens, f"'{query}' should preserve phrase '{expected_token}'"
            
            print(f"✅ PASS: '{query}' tokenized correctly: {tokens}")
    
    def test_permanent_type_removal(self):
        """Test that removal targeting permanent types includes o:permanent clause"""
        
        # Permanent types should include o:permanent clause
        permanent_removal_cases = [
            ("artifact removal", "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:artifact or o:permanent)"),
            ("creature removal", "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:creature or o:permanent)"),
            ("enchantment removal", "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:enchantment or o:permanent)"),
            ("planeswalker removal", "(o:destroy or o:\"put into\" or o:exile) and (o:creature or o:artifact or o:enchantment or o:planeswalker or o:permanent) and (o:planeswalker or o:permanent)")
        ]
        
        for query, expected_scryfall in permanent_removal_cases:
            result = extract_filters(query)
            scryfall_query = result.get("scryfall_query", "")
            
            assert scryfall_query == expected_scryfall, f"'{query}' should include permanent clause: expected {expected_scryfall}, got {scryfall_query}"
            print(f"✅ PASS: '{query}' includes permanent clause correctly")
        
        # Non-permanent types should NOT include o:permanent clause
        non_permanent_removal_cases = [
            ("land removal", "(o:destroy or o:exile or o:\"put into\") and o:land"),
            ("instant removal", "(o:destroy or o:exile or o:\"put into\") and o:instant"),
            ("sorcery removal", "(o:destroy or o:exile or o:\"put into\") and o:sorcery")
        ]
        
        for query, expected_scryfall in non_permanent_removal_cases:
            result = extract_filters(query)
            scryfall_query = result.get("scryfall_query", "")
            
            assert scryfall_query == expected_scryfall, f"'{query}' should NOT include permanent clause: expected {expected_scryfall}, got {scryfall_query}"
            print(f"✅ PASS: '{query}' correctly excludes permanent clause")
    
    def test_tricky_edge_cases(self):
        """Test tricky edge cases that might confuse regex systems"""
        
        tricky_cases = [
            # Counter vs +1/+1 counter disambiguation
            ("counter target spell", {
                "type": "instant",
                "scryfall_query": "o:\"counter target\""
            }),
            ("put +1/+1 counter on target creature", {
                "scryfall_query": "type:creature o:\"+1/+1 counter\""
            }),
            
            # Mixed signals should be handled gracefully
            ("counter spell that cannot be countered", {}),  # Should return nothing
            
            # Context-sensitive parsing
            ("blue counter magic", {
                "colors": "U",
                "type": "instant", 
                "scryfall_query": "o:\"counter target\""
            }),
            
            # Compound effects
            ("artifact that puts +1/+1 counters", {
                "scryfall_query": "type:artifact o:\"+1/+1 counter\""
            }),
            
            # Commander context overrides guild context
            ("simic ramp for my Chulane deck", {
                "coloridentity": "GWU",  # Should use Chulane's colors, not Simic
                "scryfall_query": "(o:\"search your library\" o:land) or (o:\"add\" o:\"mana\")"
            })
        ]
        
        for query, expected_filters in tricky_cases:
            result = extract_filters(query)
            
            if not expected_filters:  # Empty expected result
                assert len(result) == 0, f"'{query}' should return no filters, got {result}"
            else:
                for key, expected_value in expected_filters.items():
                    actual_value = result.get(key)
                    assert actual_value == expected_value, f"'{query}' - {key}: expected {expected_value}, got {actual_value}"
            
            print(f"✅ PASS: '{query}' handled correctly")
    
    def test_sample_queries_compatibility(self):
        """Test compatibility with frontend sample queries"""
        
        # Sample queries from the frontend that should work
        sample_queries = [
            '1 mana counterspell',
            'fetchland', 
            'azorius removal',
            '3 mana simic creature',
            'red burn spell',
            '2 mana instant',
            '4 cost artifact',
            '0 mana spell',
            'azorius counterspell',
            'simic ramp',
            'rakdos removal',
            'legendary creature',
            'artifact creature',
            'counterspell',
            'card draw',
            'ramp spell',
            'removal spell',
            'shockland',
            'dual land',
            'basic land',
            'counterspell for my Chulane deck',
            'removal for Atraxa',  # The critical failing case
            'ramp for Omnath'
        ]
        
        for query in sample_queries:
            try:
                result = extract_filters(query)
                
                # Basic validation - should return a dict with some filters
                assert isinstance(result, dict), f"'{query}' should return dict"
                assert len(result) > 0, f"'{query}' should return some filters"
                
                print(f"✅ PASS: '{query}' -> {result}")
                
            except Exception as e:
                print(f"❌ FAIL: '{query}' threw exception: {e}")
                raise


def run_all_tests():
    """Run all QueryBuilder tests"""
    test_suite = TestQueryBuilder()
    
    print("🔧 Running QueryBuilder Unit Tests...")
    print("=" * 60)
    
    try:
        test_suite.test_counter_effect_detection()
        print()
        
        test_suite.test_mana_cost_extraction()
        print()
        
        test_suite.test_color_vs_identity_logic()
        print()
        
        test_suite.test_effect_modifiers()
        print()
        
        test_suite.test_special_card_types()
        print()
        
        test_suite.test_compound_types()
        print()
        
        test_suite.test_pump_effects()
        print()
        
        test_suite.test_permanent_type_removal()
        print()
        
        test_suite.test_tokenization()
        print()
        
        test_suite.test_tricky_edge_cases()
        print()
        
        test_suite.test_sample_queries_compatibility()
        
        print("=" * 60)
        print("✅ All QueryBuilder tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
