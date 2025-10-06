"""
Data model for Magic: The Gathering decks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from src.models.card import Card

@dataclass
class DeckCard:
    """Represents a card in a deck with quantity."""
    card: Card
    quantity: int
    is_commander: bool = False  # For Commander format
    in_sideboard: bool = False  # For formats with sideboards

@dataclass
class Deck:
    """Represents a Magic: The Gathering deck."""
    name: str
    format: str  # standard, commander, modern, pauper, legacy, vintage, brawl
    description: Optional[str] = None
    
    # Cards
    cards: List[DeckCard] = field(default_factory=list)
    
    # Metadata
    colors: Optional[str] = None  # Computed from cards, e.g., "W,U,B"
    date_created: Optional[str] = None
    date_modified: Optional[str] = None
    id: Optional[int] = None
    
    # Format-specific rules
    FORMAT_RULES = {
        'standard': {'min_cards': 60, 'max_cards': None, 'max_copies': 4, 'sideboard': 15, 'commander': False},
        'commander': {'min_cards': 100, 'max_cards': 100, 'max_copies': 1, 'sideboard': 0, 'commander': True},
        'modern': {'min_cards': 60, 'max_cards': None, 'max_copies': 4, 'sideboard': 15, 'commander': False},
        'pauper': {'min_cards': 60, 'max_cards': None, 'max_copies': 4, 'sideboard': 15, 'commander': False},
        'legacy': {'min_cards': 60, 'max_cards': None, 'max_copies': 4, 'sideboard': 15, 'commander': False},
        'vintage': {'min_cards': 60, 'max_cards': None, 'max_copies': 4, 'sideboard': 15, 'commander': False},
        'brawl': {'min_cards': 60, 'max_cards': 60, 'max_copies': 1, 'sideboard': 0, 'commander': True},
    }
    
    def __post_init__(self):
        """Initialize timestamps if not set."""
        if self.date_created is None:
            self.date_created = datetime.now().isoformat()
        if self.date_modified is None:
            self.date_modified = self.date_created
    
    def get_mainboard_cards(self) -> List[DeckCard]:
        """Get all mainboard cards."""
        return [dc for dc in self.cards if not dc.in_sideboard]
    
    def get_sideboard_cards(self) -> List[DeckCard]:
        """Get all sideboard cards."""
        return [dc for dc in self.cards if dc.in_sideboard]
    
    def get_commander(self) -> Optional[DeckCard]:
        """Get the commander card (if any)."""
        for dc in self.cards:
            if dc.is_commander:
                return dc
        return None
    
    def total_cards(self, include_sideboard: bool = True) -> int:
        """Get total number of cards in deck."""
        if include_sideboard:
            return sum(dc.quantity for dc in self.cards)
        else:
            return sum(dc.quantity for dc in self.get_mainboard_cards())
    
    def mainboard_count(self) -> int:
        """Get mainboard card count."""
        return sum(dc.quantity for dc in self.get_mainboard_cards())
    
    def sideboard_count(self) -> int:
        """Get sideboard card count."""
        return sum(dc.quantity for dc in self.get_sideboard_cards())
    
    def get_colors(self) -> List[str]:
        """Compute deck colors from color identity of all cards."""
        colors_set = set()
        for deck_card in self.get_mainboard_cards():
            colors_set.update(deck_card.card.get_color_identity_list())
        return sorted(colors_set)
    
    def update_colors(self):
        """Update the deck's color identity."""
        colors = self.get_colors()
        self.colors = ','.join(colors) if colors else None
    
    def validate(self) -> List[str]:
        """
        Validate deck against format rules.
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        if self.format not in self.FORMAT_RULES:
            errors.append(f"Unknown format: {self.format}")
            return errors
        
        rules = self.FORMAT_RULES[self.format]
        mainboard = self.get_mainboard_cards()
        mainboard_count = sum(dc.quantity for dc in mainboard)
        sideboard = self.get_sideboard_cards()
        sideboard_count = sum(dc.quantity for dc in sideboard)
        
        # Check minimum deck size
        if mainboard_count < rules['min_cards']:
            errors.append(f"Deck has {mainboard_count} cards, minimum is {rules['min_cards']}")
        
        # Check maximum deck size
        if rules['max_cards'] and mainboard_count > rules['max_cards']:
            errors.append(f"Deck has {mainboard_count} cards, maximum is {rules['max_cards']}")
        
        # Check sideboard size
        if sideboard_count > rules['sideboard']:
            errors.append(f"Sideboard has {sideboard_count} cards, maximum is {rules['sideboard']}")
        
        # Check card copy limits (excluding basic lands)
        card_counts: Dict[str, int] = {}
        for dc in mainboard:
            if not dc.card.is_land() or 'Basic' not in dc.card.type_line:
                card_name = dc.card.name
                card_counts[card_name] = card_counts.get(card_name, 0) + dc.quantity
        
        for card_name, count in card_counts.items():
            if count > rules['max_copies']:
                errors.append(f"{card_name}: {count} copies (max {rules['max_copies']})")
        
        # Check commander requirements
        if rules['commander']:
            commander = self.get_commander()
            if not commander:
                errors.append("Commander format requires a commander")
            elif commander.quantity != 1:
                errors.append("Commander must have quantity of 1")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if deck is valid."""
        return len(self.validate()) == 0
    
    def add_card(self, card: Card, quantity: int = 1, is_commander: bool = False, in_sideboard: bool = False) -> bool:
        """
        Add a card to the deck.
        Returns True if successful, False if it would violate rules.
        """
        # Check if card already exists
        for dc in self.cards:
            if (dc.card.id == card.id and 
                dc.is_commander == is_commander and 
                dc.in_sideboard == in_sideboard):
                # Update quantity
                dc.quantity += quantity
                self.date_modified = datetime.now().isoformat()
                return True
        
        # Add new card
        deck_card = DeckCard(card=card, quantity=quantity, is_commander=is_commander, in_sideboard=in_sideboard)
        self.cards.append(deck_card)
        self.date_modified = datetime.now().isoformat()
        return True
    
    def remove_card(self, card: Card, quantity: int = 1, from_sideboard: bool = False) -> bool:
        """
        Remove a card from the deck.
        Returns True if successful, False if card not found.
        """
        for dc in self.cards:
            if dc.card.id == card.id and dc.in_sideboard == from_sideboard:
                if quantity >= dc.quantity:
                    self.cards.remove(dc)
                else:
                    dc.quantity -= quantity
                self.date_modified = datetime.now().isoformat()
                return True
        return False
    
    def get_mana_curve(self) -> Dict[int, int]:
        """Get mana curve distribution (CMC -> count)."""
        curve = {}
        for dc in self.get_mainboard_cards():
            if not dc.card.is_land():  # Exclude lands from mana curve
                cmc = int(dc.card.cmc) if dc.card.cmc is not None else 0
                # Cap at 7+ for display
                cmc = min(cmc, 7)
                curve[cmc] = curve.get(cmc, 0) + dc.quantity
        return curve
    
    def get_type_distribution(self) -> Dict[str, int]:
        """Get card type distribution."""
        distribution = {}
        for dc in self.get_mainboard_cards():
            types = dc.card.get_types_list()
            for card_type in types:
                distribution[card_type] = distribution.get(card_type, 0) + dc.quantity
        return distribution