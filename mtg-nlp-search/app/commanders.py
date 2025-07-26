"""
Commander database management - generates and caches commander data at startup
"""

import requests
import json
import time
from typing import Dict, Optional, List, Tuple
from functools import lru_cache

class CommanderDatabase:
    def __init__(self):
        self.commanders: Dict[str, str] = {}  # name -> color_identity
        self.commander_cards: Dict[str, dict] = {}  # name -> full card data
        self.loaded = False
    
    def load_commanders_at_startup(self) -> bool:
        """
        Load all commanders from Scryfall at server startup
        Uses a single optimized query with retry logic
        """
        print("🔄 Loading commander database from Scryfall...")
        start_time = time.time()
        
        try:
            query = "legal:commander type:legendary type:creature"
            
            commanders = {}
            page = 1
            total_cards = 0
            max_pages = 100  # Increased limit
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            print(f"🔍 Fetching commanders with query: '{query}'")
            
            while page <= max_pages and consecutive_failures < max_consecutive_failures:
                try:
                    response = requests.get(
                        "https://api.scryfall.com/cards/search",
                        params={
                            "q": query,
                            "page": page,
                            "order": "name"
                        },
                        timeout=10  # Increased timeout
                    )
                    
                    if response.status_code != 200:
                        print(f"❌ Page {page} failed with status {response.status_code}")
                        consecutive_failures += 1
                        page += 1
                        time.sleep(0.5)  # Wait longer on failure
                        continue
                    
                    data = response.json()
                    page_cards = len(data.get("data", []))
                    total_cards += page_cards
                    consecutive_failures = 0  # Reset on success
                    
                    if page % 10 == 0:  # Print progress every 10 pages
                        print(f"📄 Page {page}: {page_cards} cards (total: {total_cards})")
                    
                    for card in data.get("data", []):
                        name_key = card["name"].lower()
                        commanders[name_key] = card
                    
                    # Check if there are more pages
                    if not data.get("has_more", False):
                        print(f"✅ Completed at page {page} (no more pages)")
                        break
                        
                    page += 1
                    time.sleep(0.1)  # Rate limiting
                    
                except requests.exceptions.Timeout:
                    print(f"⏰ Page {page} timed out, retrying...")
                    consecutive_failures += 1
                    time.sleep(1)  # Wait before retry
                    continue
                    
                except Exception as e:
                    print(f"❌ Error on page {page}: {e}")
                    consecutive_failures += 1
                    page += 1
                    time.sleep(0.5)
                    continue
            
            if page > max_pages:
                print(f"⚠️  Stopped at page limit ({max_pages})")
            elif consecutive_failures >= max_consecutive_failures:
                print(f"⚠️  Stopped due to consecutive failures")
            
            # Process commanders
            print(f"🔄 Processing {len(commanders)} commanders...")
            self.commanders, self.commander_cards = self._process_commanders(commanders)
            
            self.loaded = True
            load_time = time.time() - start_time
            
            print(f"✅ Loaded {len(self.commanders)} commanders in {load_time:.2f}s")
            
            # Show some popular commanders to verify
            popular_test = ['atraxa', 'chulane', 'korvold', 'edgar', 'meren']
            found_popular = []
            for test_name in popular_test:
                for commander_key in self.commanders.keys():
                    if test_name in commander_key:
                        found_popular.append(commander_key)
                        break
            
            print(f"📋 Found popular commanders: {found_popular}")
            
            # Show alphabet coverage
            alphabet_coverage = {}
            for name in self.commanders.keys():
                first_letter = name[0].upper()
                alphabet_coverage[first_letter] = alphabet_coverage.get(first_letter, 0) + 1
            
            covered_letters = sorted(alphabet_coverage.keys())
            print(f"📝 Alphabet coverage: {covered_letters} ({len(covered_letters)}/26 letters)")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load commanders: {e}")
            self._load_fallback_commanders()
            return False
    
    def _fetch_commanders_by_query(self, query: str) -> Dict[str, dict]:
        """Fetch commanders using a Scryfall search query"""
        commanders = {}
        page = 1
        total_cards = 0
        
        print(f"🔍 Fetching commanders with query: '{query}'")
        
        while True:
            try:
                response = requests.get(
                    "https://api.scryfall.com/cards/search",
                    params={
                        "q": query,
                        "page": page,
                        "order": "name"
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"❌ Query '{query}' page {page} failed with status {response.status_code}")
                    break
                
                data = response.json()
                page_cards = len(data.get("data", []))
                total_cards += page_cards
                
                print(f"📄 Page {page}: {page_cards} cards (total so far: {total_cards})")
                
                for card in data.get("data", []):
                    # Use lowercase name as key for case-insensitive lookup
                    name_key = card["name"].lower()
                    commanders[name_key] = card
                
                # Check if there are more pages
                has_more = data.get("has_more", False)
                print(f"   Has more pages: {has_more}")
                
                if not has_more:
                    break
                    
                page += 1
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error fetching page {page} for query '{query}': {e}")
                break
        
        print(f"✅ Query '{query}' completed: {len(commanders)} unique commanders from {total_cards} total cards")
        return commanders
    
    def _process_commanders(self, raw_commanders: Dict[str, dict]) -> Tuple[Dict[str, str], Dict[str, dict]]:
        """
        Process raw commander data to create clean name->color_identity mapping
        Keeps all distinct commanders (no deduplication by base name)
        """
        commanders = {}
        commander_cards = {}
        
        # Process each commander individually - no grouping/deduplication
        for name_key, card in raw_commanders.items():
            color_identity = ''.join(card.get("color_identity", []))
            
            # Use the full lowercase name as the key
            commanders[name_key] = color_identity
            commander_cards[name_key] = card
        
        return commanders, commander_cards
    
    
    @lru_cache(maxsize=1000)
    def get_commander_colors(self, commander_name: str) -> Optional[str]:
        """
        Get color identity for a commander name
        Returns color identity string like 'WUBG' or None if not found
        """
        if not self.loaded:
            return None
        
        # Try exact match first
        name_key = commander_name.lower().strip()
        if name_key in self.commanders:
            return self.commanders[name_key]
        
        # Try partial matches (for queries like "my atraxa deck")
        for commander_key, colors in self.commanders.items():
            if commander_key in name_key or name_key in commander_key:
                return colors
        
        return None
    
    def get_commander_info(self, commander_name: str) -> Optional[dict]:
        """Get full card info for a commander"""
        name_key = commander_name.lower().strip()
        return self.commander_cards.get(name_key)
    
    def search_commanders(self, query: str, limit: int = 10) -> List[dict]:
        """Search commanders by name, return list of matches"""
        query_lower = query.lower()
        matches = []
        
        for name_key, colors in self.commanders.items():
            if query_lower in name_key:
                card_info = self.commander_cards.get(name_key, {})
                matches.append({
                    "name": card_info.get("name", name_key.title()),
                    "color_identity": colors,
                    "colors_display": self._format_colors(colors)
                })
        
        return matches[:limit]
    
    def _format_colors(self, color_identity: str) -> str:
        """Format color identity for display"""
        color_names = {
            'W': 'White',
            'U': 'Blue', 
            'B': 'Black',
            'R': 'Red',
            'G': 'Green'
        }
        
        if not color_identity:
            return "Colorless"
        
        return "/".join(color_names[c] for c in color_identity)

# Global instance
commander_db = CommanderDatabase()
