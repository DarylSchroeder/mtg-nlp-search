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
        Handles duplicates by preferring the most 'canonical' version
        """
        commanders = {}
        commander_cards = {}
        
        # Group commanders by base name (handle reprints/variants)
        name_groups = {}
        
        for name_key, card in raw_commanders.items():
            base_name = self._get_base_commander_name(card["name"])
            base_key = base_name.lower()
            
            if base_key not in name_groups:
                name_groups[base_key] = []
            name_groups[base_key].append((name_key, card))
        
        # For each group, pick the most canonical version
        for base_key, variants in name_groups.items():
            canonical_card = self._pick_canonical_commander(variants)
            
            if canonical_card:
                name_key, card = canonical_card
                color_identity = ''.join(card.get("color_identity", []))
                
                commanders[base_key] = color_identity
                commander_cards[base_key] = card
        
        return commanders, commander_cards
    
    def _get_base_commander_name(self, full_name: str) -> str:
        """
        Extract base commander name from full card name
        Examples:
        - "Atraxa, Praetors' Voice" -> "atraxa"
        - "Chulane, Teller of Tales" -> "chulane"  
        - "The Ur-Dragon" -> "the ur-dragon"
        """
        # Remove subtitle after comma
        base_name = full_name.split(',')[0].strip()
        
        # Handle special cases
        if base_name.startswith("The "):
            return base_name.lower()  # Keep "the ur-dragon"
        
        # For most commanders, use first name only
        first_name = base_name.split()[0].lower()
        
        # Special handling for multi-word names that should stay together
        multi_word_names = [
            "edgar markov", "the ur-dragon", "sliver overlord", "sliver queen",
            "child of alara", "progenitus", "jodah", "golos"
        ]
        
        full_lower = base_name.lower()
        for multi_word in multi_word_names:
            if multi_word in full_lower:
                return multi_word
        
        return first_name
    
    def _pick_canonical_commander(self, variants: List[Tuple[str, dict]]) -> Optional[Tuple[str, dict]]:
        """
        Pick the most canonical version of a commander from variants
        Prefers: original printing > recent printing > alphabetical
        """
        if not variants:
            return None
        
        if len(variants) == 1:
            return variants[0]
        
        # Scoring system for canonicalness
        def score_commander(name_key, card):
            score = 0
            
            # Prefer cards without variant suffixes
            if "//" not in card["name"]:  # Not a double-faced card
                score += 10
            
            # Prefer original printings (older sets)
            set_code = card.get("set", "").upper()
            original_sets = ["LEG", "CHR", "CMD", "C13", "C14", "C15", "C16", "C17", "C18", "C19", "C20", "C21"]
            if set_code in original_sets:
                score += 5
            
            # Prefer non-promo versions
            if not card.get("promo", False):
                score += 3
            
            # Prefer English cards
            if card.get("lang", "en") == "en":
                score += 2
            
            # Prefer cards with shorter names (less likely to be variants)
            score -= len(card["name"]) * 0.01
            
            return score
        
        # Sort by score (highest first)
        scored_variants = [(score_commander(name_key, card), name_key, card) for name_key, card in variants]
        scored_variants.sort(reverse=True)
        
        return (scored_variants[0][1], scored_variants[0][2])
    
    def _load_fallback_commanders(self):
        """Fallback to comprehensive list of popular commanders if API fails"""
        fallback_commanders = {
            # Popular 5-color commanders
            'kenrith': 'WUBRG',
            'golos': 'WUBRG',
            'the ur-dragon': 'WUBRG',
            'jodah': 'WUBRG',
            'sliver overlord': 'WUBRG',
            'sliver queen': 'WUBRG',
            'child of alara': 'WUBRG',
            'progenitus': 'WUBRG',
            
            # Popular 4-color commanders
            'atraxa': 'WUBG',
            'breya': 'WUBR',
            'yidris': 'UBRG',
            'kynaios': 'WURG',
            
            # Popular 3-color commanders
            'chulane': 'GUW',
            'korvold': 'BRG',
            'edgar markov': 'RWB',
            'muldrotha': 'UBG',
            'alesha': 'RWB',
            'animar': 'URG',
            'karador': 'WBG',
            'ghave': 'WBG',
            'derevi': 'GUW',
            'prossh': 'BRG',
            'marath': 'RGW',
            'roon': 'GUW',
            'nekusar': 'UBR',
            'jeleva': 'UBR',
            'oloro': 'WUB',
            'sharuum': 'WUB',
            'zur': 'WUB',
            'rafiq': 'GUW',
            'uril': 'RGW',
            'mayael': 'RGW',
            'kresh': 'BRG',
            'sedris': 'UBR',
            'thraximundar': 'UBR',
            
            # Popular 2-color commanders
            'meren': 'BG',
            'ayli': 'WB',
            'karlov': 'WB',
            'teysa': 'WB',
            'athreos': 'WB',
            'daxos': 'WB',
            'kambal': 'WB',
            'vish kal': 'WB',
            'selenia': 'WB',
            'arvad': 'WB',
            'trynn': 'WB',
            'silvar': 'WB',
            
            'azami': 'U',
            'talrand': 'U',
            'baral': 'U',
            'jace': 'U',
            'teferi': 'U',
            'urza': 'U',
            'memnarch': 'U',
            
            'krenko': 'R',
            'purphoros': 'R',
            'daretti': 'R',
            'feldon': 'R',
            'neheb': 'R',
            'etali': 'R',
            'zada': 'R',
            'krark': 'R',
            
            'ezuri': 'G',
            'omnath': 'G',
            'azusa': 'G',
            'selvala': 'G',
            'yisan': 'G',
            'freyalise': 'G',
            'titania': 'G',
            'kamahl': 'G',
            
            'mikaeus': 'B',
            'sheoldred': 'B',
            'chainer': 'B',
            'erebos': 'B',
            'xiahou dun': 'B',
            'gonti': 'B',
            'yahenni': 'B',
            'kokusho': 'B',
            
            'elesh norn': 'W',
            'avacyn': 'W',
            'heliod': 'W',
            'darien': 'W',
            'odric': 'W',
            'thalia': 'W',
            'lin sivvi': 'W',
            'hokori': 'W',
            
            # Colorless commanders
            'kozilek': '',
            'ulamog': '',
            'emrakul': '',
            'karn': '',
            'hope of ghirapur': '',
            'traxos': '',
        }
        
        self.commanders = fallback_commanders
        self.loaded = True
        print(f"⚠️  Using comprehensive fallback commander list ({len(fallback_commanders)} commanders)")
        
        # Show what we have
        popular_test = ['atraxa', 'chulane', 'korvold', 'edgar', 'meren']
        found_popular = [name for name in popular_test if name in self.commanders or any(name in key for key in self.commanders.keys())]
        print(f"📋 Fallback includes popular commanders: {found_popular}")
    
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
