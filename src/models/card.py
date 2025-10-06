"""
Data model for Magic: The Gathering cards.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Card:
    """Represents a Magic: The Gathering card in the collection."""
    
    # Basic identification
    name: str
    set_code: str
    collector_number: str
    
    # Collection details
    quantity: int = 1
    condition: Optional[str] = None
    language: str = "en"
    foil: bool = False
    
    # Pricing
    purchase_price: Optional[float] = None
    current_price: Optional[float] = None
    
    # Scryfall data
    scryfall_id: Optional[str] = None
    oracle_id: Optional[str] = None
    rarity: Optional[str] = None
    
    # Gameplay data
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    colors: Optional[str] = None  # Comma-separated: "W,U,B,R,G"
    color_identity: Optional[str] = None  # For Commander
    type_line: Optional[str] = None
    card_types: Optional[str] = None  # Comma-separated: "Creature,Legendary"
    subtypes: Optional[str] = None  # Comma-separated: "Human,Wizard"
    oracle_text: Optional[str] = None
    
    # Metadata
    tags: Optional[str] = None
    notes: Optional[str] = None
    date_added: Optional[str] = None
    id: Optional[int] = None
    
    def get_colors_list(self) -> List[str]:
        """Get colors as a list."""
        if not self.colors:
            return []
        return [c.strip() for c in self.colors.split(',') if c.strip()]
    
    def get_color_identity_list(self) -> List[str]:
        """Get color identity as a list."""
        if not self.color_identity:
            return []
        return [c.strip() for c in self.color_identity.split(',') if c.strip()]
    
    def get_types_list(self) -> List[str]:
        """Get card types as a list."""
        if not self.card_types:
            return []
        return [t.strip() for t in self.card_types.split(',') if t.strip()]
    
    def get_subtypes_list(self) -> List[str]:
        """Get subtypes as a list."""
        if not self.subtypes:
            return []
        return [s.strip() for s in self.subtypes.split(',') if s.strip()]
    
    def is_creature(self) -> bool:
        """Check if card is a creature."""
        return 'Creature' in self.get_types_list()
    
    def is_land(self) -> bool:
        """Check if card is a land."""
        return 'Land' in self.get_types_list()
    
    def is_instant_or_sorcery(self) -> bool:
        """Check if card is an instant or sorcery."""
        types = self.get_types_list()
        return 'Instant' in types or 'Sorcery' in types