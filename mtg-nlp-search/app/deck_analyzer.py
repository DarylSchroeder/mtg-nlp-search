"""
MTG Deck Analyzer Integration
For integration with the MTG NLP Search API
"""

import requests
import time
from typing import Dict, List, Optional

class DeckAnalyzer:
    def __init__(self):
        self.scryfall_base = "https://api.scryfall.com"
        
        # Known underpowered cards with better alternatives
        self.underpowered_cards = {
            "Murder": {
                "alternatives": ["Swords to Plowshares", "Path to Exile", "Generous Gift"], 
                "reason": "3 mana for single target removal is inefficient"
            },
            "Cancel": {
                "alternatives": ["Counterspell", "Negate", "Swan Song"], 
                "reason": "3 mana counterspell with no upside"
            },
            "Doom Blade": {
                "alternatives": ["Fatal Push", "Go for the Throat", "Heartless Act"], 
                "reason": "Too restrictive (non-black creatures only)"
            },
            "Terror": {
                "alternatives": ["Fatal Push", "Go for the Throat", "Heartless Act"], 
                "reason": "Too restrictive (non-artifact, non-black)"
            },
            "Lightning Strike": {
                "alternatives": ["Lightning Bolt", "Shock", "Galvanic Blast"], 
                "reason": "3 mana for 3 damage is below rate"
            },
            "Shock": {
                "alternatives": ["Lightning Bolt", "Galvanic Blast", "Burst Lightning"], 
                "reason": "Only 2 damage for 1 mana"
            },
            "Divination": {
                "alternatives": ["Rhystic Study", "Mystic Remora", "Phyrexian Arena"], 
                "reason": "3 mana for 2 cards is below rate"
            },
            "Essence Scatter": {
                "alternatives": ["Counterspell", "Mana Drain", "Force of Will"], 
                "reason": "Too narrow (creatures only)"
            }
        }
    
    def get_card_data(self, card_name: str) -> Optional[Dict]:
        """Fetch card data from Scryfall with rate limiting"""
        try:
            url = f"{self.scryfall_base}/cards/named"
            params = {"fuzzy": card_name}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.RequestException:
            return None
    
    def analyze_card(self, card_name: str) -> Dict:
        """Analyze a single card for power level and alternatives"""
        # Check if it's a known underpowered card first
        if card_name in self.underpowered_cards:
            card_info = self.underpowered_cards[card_name]
            return {
                "name": card_name,
                "power_level": "low",
                "reason": card_info["reason"],
                "alternatives": card_info["alternatives"],
                "needs_improvement": True
            }
        
        # Get Scryfall data for EDHREC rank
        card_data = self.get_card_data(card_name)
        if not card_data:
            return {
                "name": card_name,
                "power_level": "unknown",
                "reason": "Card not found",
                "alternatives": [],
                "needs_improvement": False
            }
        
        analysis = {
            "name": card_data.get("name", card_name),
            "cmc": card_data.get("cmc", 0),
            "type_line": card_data.get("type_line", ""),
            "power_level": "medium",
            "reason": "",
            "alternatives": [],
            "needs_improvement": False
        }
        
        # Use EDHREC rank for power assessment
        edhrec_rank = card_data.get("edhrec_rank")
        if edhrec_rank:
            if edhrec_rank < 1000:
                analysis["power_level"] = "high"
                analysis["reason"] = f"EDHREC rank {edhrec_rank} - staple card"
            elif edhrec_rank < 5000:
                analysis["power_level"] = "medium"
                analysis["reason"] = f"EDHREC rank {edhrec_rank} - playable"
            else:
                analysis["power_level"] = "low"
                analysis["reason"] = f"EDHREC rank {edhrec_rank} - rarely played"
                analysis["needs_improvement"] = True
                analysis["alternatives"] = self.suggest_alternatives_by_function(card_data)
        
        return analysis
    
    def suggest_alternatives_by_function(self, card_data: Dict) -> List[str]:
        """Suggest alternatives based on card function"""
        type_line = card_data.get("type_line", "").lower()
        oracle_text = card_data.get("oracle_text", "").lower()
        
        # Removal spells
        if ("instant" in type_line or "sorcery" in type_line) and \
           any(word in oracle_text for word in ["destroy", "exile", "damage"]):
            return ["Swords to Plowshares", "Path to Exile", "Generous Gift"]
        
        # Counterspells
        if "counter" in oracle_text and "spell" in oracle_text:
            return ["Counterspell", "Negate", "Swan Song"]
        
        # Card draw
        if "draw" in oracle_text and "card" in oracle_text:
            return ["Rhystic Study", "Mystic Remora", "Phyrexian Arena"]
        
        return []
    
    def analyze_deck_list(self, card_names: List[str], max_cards: int = 20) -> Dict:
        """Analyze a list of cards and return improvement suggestions"""
        results = {
            "total_analyzed": 0,
            "improvements": [],
            "summary": {
                "high_power": 0,
                "medium_power": 0,
                "low_power": 0,
                "needs_improvement": 0
            }
        }
        
        # Limit analysis to prevent API rate limiting
        cards_to_analyze = card_names[:max_cards]
        
        for card_name in cards_to_analyze:
            analysis = self.analyze_card(card_name)
            results["total_analyzed"] += 1
            
            # Update summary
            power_level = analysis.get("power_level", "unknown")
            if power_level in results["summary"]:
                results["summary"][power_level] += 1
            
            # Add to improvements if needs improvement
            if analysis.get("needs_improvement") and analysis.get("alternatives"):
                results["improvements"].append({
                    "card": analysis["name"],
                    "reason": analysis["reason"],
                    "alternatives": analysis["alternatives"]
                })
                results["summary"]["needs_improvement"] += 1
            
            # Rate limiting for Scryfall API
            time.sleep(0.1)
        
        return results
