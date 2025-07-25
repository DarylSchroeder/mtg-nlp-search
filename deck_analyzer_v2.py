#!/usr/bin/env python3
"""
MTG Deck Analyzer - Practical Version
Uses Scryfall data and manual deck input to suggest improvements
"""

import requests
import json
import time
from typing import Dict, List, Optional

class DeckAnalyzer:
    def __init__(self):
        self.scryfall_base = "https://api.scryfall.com"
        
        # Known underpowered cards by category
        self.underpowered_cards = {
            "removal": {
                "Murder": {"alternatives": ["Swords to Plowshares", "Path to Exile", "Generous Gift"], "reason": "3 mana for single target removal is inefficient"},
                "Doom Blade": {"alternatives": ["Fatal Push", "Go for the Throat", "Heartless Act"], "reason": "Too many restrictions (non-black)"},
                "Terror": {"alternatives": ["Fatal Push", "Go for the Throat", "Heartless Act"], "reason": "Too many restrictions (non-artifact, non-black)"},
                "Lightning Strike": {"alternatives": ["Lightning Bolt", "Shock", "Galvanic Blast"], "reason": "3 mana for 3 damage is below rate"},
                "Shock": {"alternatives": ["Lightning Bolt", "Galvanic Blast", "Burst Lightning"], "reason": "Only 2 damage for 1 mana"},
            },
            "counterspells": {
                "Cancel": {"alternatives": ["Counterspell", "Negate", "Swan Song"], "reason": "3 mana counterspell with no upside"},
                "Essence Scatter": {"alternatives": ["Counterspell", "Mana Drain", "Force of Will"], "reason": "Too narrow (creatures only)"},
            },
            "card_draw": {
                "Divination": {"alternatives": ["Rhystic Study", "Mystic Remora", "Phyrexian Arena"], "reason": "3 mana for 2 cards is below rate"},
            }
        }
        
        # Format-specific staples
        self.format_staples = {
            "commander": {
                "removal": ["Swords to Plowshares", "Path to Exile", "Generous Gift", "Beast Within", "Chaos Warp", "Anguished Unmaking", "Assassin's Trophy", "Cyclonic Rift"],
                "ramp": ["Sol Ring", "Arcane Signet", "Command Tower", "Cultivate", "Kodama's Reach", "Rampant Growth"],
                "card_draw": ["Rhystic Study", "Mystic Remora", "Phyrexian Arena", "Sylvan Library", "Necropotence"]
            },
            "standard": {
                "removal": ["Cut Down", "Go for the Throat", "Destroy Evil", "Farewell", "The Wandering Emperor"],
                "counterspells": ["Negate", "Essence Scatter", "Make Disappear"],
                "card_draw": ["Consider", "Expressive Iteration", "Divination"]
            }
        }
    
    def get_card_data(self, card_name: str) -> Optional[Dict]:
        """Fetch card data from Scryfall"""
        try:
            url = f"{self.scryfall_base}/cards/named"
            params = {"fuzzy": card_name}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except requests.RequestException:
            return None
    
    def analyze_card(self, card_name: str, deck_format: str = "commander") -> Dict:
        """Analyze a single card and suggest improvements"""
        card_data = self.get_card_data(card_name)
        if not card_data:
            return {"error": f"Card not found: {card_name}"}
        
        analysis = {
            "name": card_data.get("name"),
            "cmc": card_data.get("cmc", 0),
            "type_line": card_data.get("type_line"),
            "power_level": "unknown",
            "issues": [],
            "alternatives": [],
            "edhrec_rank": card_data.get("edhrec_rank")
        }
        
        # Check if it's a known underpowered card
        for category, cards in self.underpowered_cards.items():
            if card_name in cards:
                card_info = cards[card_name]
                analysis["power_level"] = "low"
                analysis["issues"].append(card_info["reason"])
                analysis["alternatives"] = card_info["alternatives"]
                break
        
        # Use EDHREC rank as power level indicator
        if analysis["edhrec_rank"]:
            rank = analysis["edhrec_rank"]
            if rank < 1000:
                if analysis["power_level"] == "unknown":
                    analysis["power_level"] = "high"
                analysis["issues"].append(f"EDHREC rank: {rank} (staple card)")
            elif rank < 5000:
                if analysis["power_level"] == "unknown":
                    analysis["power_level"] = "medium"
            else:
                if analysis["power_level"] == "unknown":
                    analysis["power_level"] = "low"
                analysis["issues"].append(f"EDHREC rank: {rank} (rarely played)")
        
        # Suggest format-appropriate alternatives if card is underpowered
        if analysis["power_level"] == "low" and not analysis["alternatives"]:
            analysis["alternatives"] = self.suggest_alternatives_by_type(card_data, deck_format)
        
        return analysis
    
    def suggest_alternatives_by_type(self, card_data: Dict, deck_format: str) -> List[str]:
        """Suggest alternatives based on card type and format"""
        type_line = card_data.get("type_line", "").lower()
        oracle_text = card_data.get("oracle_text", "").lower()
        
        alternatives = []
        
        # Identify card function and suggest alternatives
        if "instant" in type_line or "sorcery" in type_line:
            if any(word in oracle_text for word in ["destroy", "exile", "damage"]):
                alternatives = self.format_staples.get(deck_format, {}).get("removal", [])
            elif "counter" in oracle_text:
                alternatives = self.format_staples.get(deck_format, {}).get("counterspells", [])
            elif "draw" in oracle_text:
                alternatives = self.format_staples.get(deck_format, {}).get("card_draw", [])
        
        return alternatives[:3]  # Return top 3
    
    def analyze_deck_list(self, deck_list: List[str], deck_format: str = "commander") -> Dict:
        """Analyze a list of card names"""
        results = {
            "format": deck_format,
            "total_cards": len(deck_list),
            "analyzed_cards": [],
            "improvements": [],
            "summary": {
                "high_power": 0,
                "medium_power": 0,
                "low_power": 0,
                "needs_improvement": 0
            }
        }
        
        for card_name in deck_list:
            print(f"Analyzing: {card_name}")
            analysis = self.analyze_card(card_name, deck_format)
            
            if "error" not in analysis:
                results["analyzed_cards"].append(analysis)
                
                # Update summary
                power_level = analysis.get("power_level", "unknown")
                if power_level in results["summary"]:
                    results["summary"][power_level] += 1
                
                # Add to improvements if low power
                if power_level == "low" and analysis.get("alternatives"):
                    results["improvements"].append({
                        "card": analysis["name"],
                        "issues": analysis["issues"],
                        "alternatives": analysis["alternatives"]
                    })
                    results["summary"]["needs_improvement"] += 1
            
            # Rate limiting for Scryfall API
            time.sleep(0.1)
        
        return results

# Example usage with a sample Standard deck
if __name__ == "__main__":
    analyzer = DeckAnalyzer()
    
    # Sample Standard deck cards (some intentionally underpowered for demo)
    sample_deck = [
        "Murder",           # Underpowered removal
        "Cancel",           # Underpowered counterspell  
        "Shock",            # Underpowered burn
        "Lightning Strike", # Underpowered burn
        "Divination",       # Underpowered card draw
        "Counterspell",     # Good card
        "Lightning Bolt",   # Good card
        "Swords to Plowshares", # Excellent card
    ]
    
    print("Analyzing sample deck...")
    results = analyzer.analyze_deck_list(sample_deck, "standard")
    
    print("\n" + "="*50)
    print("DECK ANALYSIS RESULTS")
    print("="*50)
    
    print(f"Format: {results['format']}")
    print(f"Total cards analyzed: {results['total_cards']}")
    print(f"Cards needing improvement: {results['summary']['needs_improvement']}")
    
    print("\nIMPROVEMENT SUGGESTIONS:")
    print("-" * 30)
    
    for improvement in results["improvements"]:
        print(f"\n🔄 {improvement['card']}")
        for issue in improvement["issues"]:
            print(f"   ❌ {issue}")
        print(f"   ✅ Consider: {', '.join(improvement['alternatives'])}")
    
    print(f"\nPower Level Distribution:")
    print(f"   High: {results['summary']['high_power']}")
    print(f"   Medium: {results['summary']['medium_power']}")  
    print(f"   Low: {results['summary']['low_power']}")
