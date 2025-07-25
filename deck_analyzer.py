#!/usr/bin/env python3
"""
MTG Deck Analyzer - Proof of Concept
Analyzes Moxfield decks and suggests improvements using EDHREC/Scryfall data
"""

import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

class DeckAnalyzer:
    def __init__(self):
        self.scryfall_base = "https://api.scryfall.com"
        self.moxfield_base = "https://api2.moxfield.com/v3"
        self.edhrec_base = "https://edhrec-json.s3.amazonaws.com"
    
    def extract_deck_id(self, moxfield_url: str) -> Optional[str]:
        """Extract deck ID from Moxfield URL"""
        # Handle various Moxfield URL formats
        patterns = [
            r'moxfield\.com/decks/([a-zA-Z0-9_-]+)',
            r'moxfield\.com/decks/([a-zA-Z0-9_-]+)/',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, moxfield_url)
            if match:
                return match.group(1)
        return None
    
    def fetch_moxfield_deck(self, deck_id: str) -> Optional[Dict]:
        """Fetch deck data from Moxfield API"""
        try:
            url = f"{self.moxfield_base}/decks/{deck_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching Moxfield deck: {e}")
            return None
    
    def get_edhrec_data(self, commander_name: str) -> Optional[Dict]:
        """Fetch EDHREC recommendations for a commander"""
        try:
            # Convert commander name to EDHREC format
            edhrec_name = commander_name.lower().replace(' ', '-').replace(',', '').replace("'", '')
            url = f"{self.edhrec_base}/commanders/{edhrec_name}.json"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching EDHREC data for {commander_name}: {e}")
            return None
    
    def analyze_card_power_level(self, card_name: str, format_type: str, commander: str = None) -> Dict:
        """Analyze a card's power level and suggest alternatives"""
        try:
            # Get card data from Scryfall
            url = f"{self.scryfall_base}/cards/named"
            params = {"fuzzy": card_name}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {"error": f"Card not found: {card_name}"}
            
            card_data = response.json()
            
            analysis = {
                "name": card_data.get("name"),
                "cmc": card_data.get("cmc", 0),
                "type_line": card_data.get("type_line"),
                "power_level": "unknown",
                "reasons": [],
                "alternatives": []
            }
            
            # Basic power level heuristics
            if card_data.get("edhrec_rank"):
                rank = card_data["edhrec_rank"]
                if rank < 1000:
                    analysis["power_level"] = "high"
                    analysis["reasons"].append(f"EDHREC rank: {rank} (staple)")
                elif rank < 5000:
                    analysis["power_level"] = "medium"
                    analysis["reasons"].append(f"EDHREC rank: {rank} (playable)")
                else:
                    analysis["power_level"] = "low"
                    analysis["reasons"].append(f"EDHREC rank: {rank} (fringe)")
            
            # Check for obvious underpowered cards
            if self.is_underpowered_removal(card_data):
                analysis["power_level"] = "low"
                analysis["reasons"].append("Inefficient removal spell")
                analysis["alternatives"] = self.suggest_removal_alternatives(card_data, format_type)
            
            return analysis
            
        except requests.RequestException as e:
            return {"error": f"Error analyzing {card_name}: {e}"}
    
    def is_underpowered_removal(self, card_data: Dict) -> bool:
        """Identify underpowered removal spells"""
        name = card_data.get("name", "").lower()
        type_line = card_data.get("type_line", "").lower()
        cmc = card_data.get("cmc", 0)
        
        # Examples of underpowered removal
        underpowered_removal = [
            "shock", "lightning strike", "murder", "doom blade", 
            "terror", "dark banishing", "disenchant"
        ]
        
        if name in underpowered_removal:
            return True
        
        # High CMC single-target removal
        if "instant" in type_line or "sorcery" in type_line:
            if cmc >= 4 and any(word in card_data.get("oracle_text", "").lower() 
                              for word in ["destroy target", "exile target"]):
                return True
        
        return False
    
    def suggest_removal_alternatives(self, card_data: Dict, format_type: str) -> List[str]:
        """Suggest better removal alternatives"""
        alternatives = []
        
        if format_type.lower() == "commander":
            alternatives = [
                "Swords to Plowshares", "Path to Exile", "Generous Gift",
                "Beast Within", "Chaos Warp", "Anguished Unmaking",
                "Assassin's Trophy", "Vindicate", "Cyclonic Rift"
            ]
        elif format_type.lower() == "standard":
            # Would need to check current Standard legality
            alternatives = [
                "Cut Down", "Go for the Throat", "Destroy Evil",
                "Farewell", "The Wandering Emperor"
            ]
        
        return alternatives[:3]  # Return top 3 suggestions
    
    def analyze_deck(self, moxfield_url: str) -> Dict:
        """Main analysis function"""
        deck_id = self.extract_deck_id(moxfield_url)
        if not deck_id:
            return {"error": "Invalid Moxfield URL"}
        
        deck_data = self.fetch_moxfield_deck(deck_id)
        if not deck_data:
            return {"error": "Could not fetch deck data"}
        
        # Extract basic deck info
        deck_info = {
            "name": deck_data.get("name", "Unknown"),
            "format": deck_data.get("format", "Unknown"),
            "commander": None,
            "total_cards": 0,
            "analysis": [],
            "suggestions": []
        }
        
        # Get commander info
        commanders = deck_data.get("commanders", {})
        if commanders:
            commander_card = list(commanders.values())[0]
            deck_info["commander"] = commander_card.get("card", {}).get("name")
        
        # Analyze mainboard cards
        mainboard = deck_data.get("mainboard", {})
        deck_info["total_cards"] = sum(card_info.get("quantity", 0) for card_info in mainboard.values())
        
        # Sample analysis of first 10 cards (for demo)
        analyzed_count = 0
        for card_id, card_info in mainboard.items():
            if analyzed_count >= 10:  # Limit for demo
                break
                
            card_name = card_info.get("card", {}).get("name")
            if card_name:
                analysis = self.analyze_card_power_level(
                    card_name, 
                    deck_info["format"], 
                    deck_info["commander"]
                )
                
                if analysis.get("power_level") == "low":
                    deck_info["analysis"].append(analysis)
                
                analyzed_count += 1
        
        return deck_info

# Example usage
if __name__ == "__main__":
    analyzer = DeckAnalyzer()
    
    # Test with the provided deck
    test_url = "https://moxfield.com/decks/Wk_LgCIkS0KVHIPRxj1zbg"
    result = analyzer.analyze_deck(test_url)
    
    print(json.dumps(result, indent=2))
