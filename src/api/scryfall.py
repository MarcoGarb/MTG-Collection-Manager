"""
Scryfall API integration for fetching card data and prices.
"""
import requests
import time
from typing import Optional, Dict
from datetime import datetime


class ScryfallAPI:
    """Client for interacting with Scryfall API."""
    
    BASE_URL = "https://api.scryfall.com"
    RATE_LIMIT_DELAY = 0.1  # 100ms between requests (Scryfall asks for 50-100ms)
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MTG Collection Manager/1.0'
        })
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed Scryfall's rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited request to Scryfall API."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Scryfall API error: {e}")
            return None
            
    def get_card_by_set_and_number(self, set_code: str, collector_number: str) -> Optional[Dict]:
        """
        Fetch card data by set code and collector number.
        This is the most accurate way to match cards.
        """
        endpoint = f"/cards/{set_code.lower()}/{collector_number}"
        return self._make_request(endpoint)
        
    def get_card_by_name(self, card_name: str, set_code: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch card data by name, optionally filtered by set.
        """
        endpoint = "/cards/named"
        params = {'exact': card_name}
        if set_code:
            params['set'] = set_code.lower()
        return self._make_request(endpoint, params)
        
    def search_cards(self, query: str) -> Optional[Dict]:
        """
        Search for cards using Scryfall syntax.
        Example: "name:lightning set:lea"
        """
        endpoint = "/cards/search"
        params = {'q': query}
        return self._make_request(endpoint, params)
        
    def extract_price_from_card(self, card_data: Dict, foil: bool = False) -> Optional[float]:
        """
        Extract USD price from Scryfall card data.
        Returns None if price is not available.
        """
        if not card_data or 'prices' not in card_data:
            return None
            
        prices = card_data['prices']
        
        if foil:
            price_str = prices.get('usd_foil')
        else:
            price_str = prices.get('usd')
            
        if price_str and price_str != 'null':
            try:
                return float(price_str)
            except ValueError:
                return None
        return None
        
    def extract_card_details(self, card_data: Dict) -> Dict:
        """
        Extract useful information from Scryfall card data.
        """
        if not card_data:
            return {}
            
        details = {
            'scryfall_id': card_data.get('id'),
            'oracle_id': card_data.get('oracle_id'),
            'name': card_data.get('name'),
            'set_code': card_data.get('set'),
            'collector_number': card_data.get('collector_number'),
            'rarity': card_data.get('rarity'),
            'mana_cost': card_data.get('mana_cost'),
            'cmc': card_data.get('cmc'),
            'type_line': card_data.get('type_line'),
            'oracle_text': card_data.get('oracle_text'),
            'colors': card_data.get('colors', []),
            'color_identity': card_data.get('color_identity', []),
            'image_uris': card_data.get('image_uris', {}),
            'prices': card_data.get('prices', {}),
            'legalities': card_data.get('legalities', {}),
            'released_at': card_data.get('released_at'),
            'scryfall_uri': card_data.get('scryfall_uri'),
        }
        
        # Handle double-faced cards
        if 'card_faces' in card_data and card_data['card_faces']:
            details['card_faces'] = card_data['card_faces']
            # Use first face's image if main image_uris not available
            if not details['image_uris'] and 'image_uris' in card_data['card_faces'][0]:
                details['image_uris'] = card_data['card_faces'][0]['image_uris']
        
        return details
        
    def get_card_image_url(self, card_data: Dict, size: str = 'normal') -> Optional[str]:
        """
        Get image URL for a card.
        Sizes: small, normal, large, png, art_crop, border_crop
        """
        if not card_data:
            return None
            
        image_uris = card_data.get('image_uris', {})
        
        # Handle double-faced cards
        if not image_uris and 'card_faces' in card_data:
            faces = card_data.get('card_faces', [])
            if faces and 'image_uris' in faces[0]:
                image_uris = faces[0]['image_uris']
                
        return image_uris.get(size)