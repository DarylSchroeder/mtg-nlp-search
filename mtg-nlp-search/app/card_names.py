"""
Card names cache for lookahead functionality
"""
import requests
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class CardNamesCache:
    def __init__(self):
        self.card_names: List[str] = []
        self.loaded = False
        
    def load_card_names(self):
        """Load card names from Scryfall API on startup (synchronous)"""
        try:
            logger.info("Loading card names from Scryfall...")
            response = requests.get("https://api.scryfall.com/catalog/card-names", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.card_names = data.get('data', [])
                self.loaded = True
                logger.info(f"Loaded {len(self.card_names)} card names successfully")
            else:
                logger.error(f"Failed to load card names: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error loading card names: {e}")
            # Set empty list as fallback
            self.card_names = []
            self.loaded = False
    
    def search_card_names(self, query: str, limit: int = 10) -> List[str]:
        """
        Search for card names that start with the query string
        Returns up to 'limit' matches
        """
        if not self.loaded or not query:
            return []
            
        query_lower = query.lower()
        matches = []
        
        for name in self.card_names:
            if name.lower().startswith(query_lower):
                matches.append(name)
                if len(matches) >= limit:
                    break
                    
        return matches
    
    def is_exact_card_name(self, query: str) -> bool:
        """Check if the query is an exact card name match"""
        if not self.loaded:
            return False
        return query in self.card_names

# Global instance
card_names_cache = CardNamesCache()
