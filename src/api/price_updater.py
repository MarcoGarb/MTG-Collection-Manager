"""
Update card prices from Scryfall API.
"""
from typing import List, Callable, Optional
from src.models.card import Card
from src.api.scryfall import ScryfallAPI
from src.data.database import DatabaseManager


class PriceUpdater:
    """Update card prices from Scryfall."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.api = ScryfallAPI()
        
    def update_card_price(self, card: Card) -> bool:
        """
        Update a single card's price from Scryfall.
        Returns True if successful.
        """
        try:
            # Fetch card data using set and collector number (most accurate)
            card_data = self.api.get_card_by_set_and_number(
                card.set_code,
                card.collector_number
            )
            
            if not card_data:
                print(f"  ⚠ Not found on Scryfall: {card.name} [{card.set_code}]")
                return False
                
            # Extract price
            price = self.api.extract_price_from_card(card_data, card.foil)
            
            if price is not None:
                # Update card price in database
                self.db.cursor.execute("""
                    UPDATE cards 
                    SET current_price = ?, scryfall_id = ?
                    WHERE id = ?
                """, (price, card_data.get('id'), card.id))
                self.db.connection.commit()
                
                print(f"  ✓ {card.name}: ${price:.2f}")
                return True
            else:
                print(f"  ⚠ No price available: {card.name}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error updating {card.name}: {e}")
            return False
            
    def update_all_prices(self, progress_callback: Optional[Callable] = None) -> dict:
        """
        Update prices for all cards in the collection.
        Also updates gameplay data (colors, types, mana cost, etc.)
    
        Args:
            progress_callback: Optional function(current, total, card_name) to report progress
        
        Returns:
            dict with statistics about the update
        """
        cards = self.db.get_all_cards()
        total = len(cards)
    
        stats = {
            'total': total,
            'updated': 0,
            'not_found': 0,
            'no_price': 0,
            'errors': 0
        }
    
        print(f"\nUpdating prices and gameplay data for {total} cards...")
        print("=" * 60)
    
        for i, card in enumerate(cards, 1):
            if progress_callback:
                progress_callback(i, total, card.name)
            
            try:
                card_data = self.api.get_card_by_set_and_number(
                    card.set_code,
                    card.collector_number
                )
            
                if not card_data:
                    stats['not_found'] += 1
                    continue
                
                # Extract price
                price = self.api.extract_price_from_card(card_data, card.foil)
            
                # Extract gameplay data
                colors = ','.join(card_data.get('colors', []))
                color_identity = ','.join(card_data.get('color_identity', []))
            
                # Extract card types and subtypes from type_line
                type_line = card_data.get('type_line', '')
                card_types = []
                subtypes = []
            
                if type_line:
                    # Split by '—' to separate types from subtypes
                    parts = type_line.split('—')
                    type_part = parts[0].strip()
                
                    # Extract main types
                    for t in ['Legendary', 'Artifact', 'Creature', 'Enchantment', 'Instant', 
                              'Sorcery', 'Planeswalker', 'Land', 'Tribal', 'Battle']:
                        if t in type_part:
                            card_types.append(t)
                
                    # Extract subtypes
                    if len(parts) > 1:
                        subtype_part = parts[1].strip()
                        subtypes = [s.strip() for s in subtype_part.split() if s.strip()]
            
                card_types_str = ','.join(card_types) if card_types else None
                subtypes_str = ','.join(subtypes) if subtypes else None
            
                # Update database with price AND gameplay data
                self.db.cursor.execute("""
                    UPDATE cards 
                    SET current_price = ?, 
                        scryfall_id = ?,
                        mana_cost = ?,
                        cmc = ?,
                        colors = ?,
                        color_identity = ?,
                        type_line = ?,
                        card_types = ?,
                        subtypes = ?,
                        oracle_text = ?
                    WHERE id = ?
                """, (
                    price, 
                    card_data.get('id'),
                    card_data.get('mana_cost'),
                    card_data.get('cmc'),
                    colors if colors else None,
                    color_identity if color_identity else None,
                    type_line if type_line else None,
                    card_types_str,
                    subtypes_str,
                    card_data.get('oracle_text'),
                    card.id
                ))
            
                if price is not None:
                    stats['updated'] += 1
                else:
                    stats['no_price'] += 1
                
            except Exception as e:
                print(f"  Error with {card.name}: {e}")
                stats['errors'] += 1
                continue
            
        self.db.connection.commit()
    
        print("=" * 60)
        print(f"✓ Updated: {stats['updated']}")
        print(f"⚠ Not found: {stats['not_found']}")
        print(f"⚠ No price: {stats['no_price']}")
        print(f"✗ Errors: {stats['errors']}")
    
        return stats