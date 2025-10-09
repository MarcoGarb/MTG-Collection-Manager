"""
Data model for Magic: The Gathering cube drafts.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
from src.models.card import Card

@dataclass
class CubeCard:
    """Represents a card in a cube with additional cube-specific metadata."""
    card: Card
    quantity: int = 1  # Usually 1 for cube, but can be more for lands
    is_basic_land: bool = False  # For basic lands that can be unlimited
    cube_notes: Optional[str] = None  # Personal notes about the card in this cube

@dataclass
class Cube:
    """Represents a Magic: The Gathering cube for drafting."""
    name: str
    description: Optional[str] = None
    size: int = 360  # Standard cube size (can be 180, 360, 450, 540, etc.)
    format: str = "vintage"  # Format the cube is designed for
    
    # Cards
    cards: List[CubeCard] = field(default_factory=list)
    
    # Metadata
    colors: Optional[str] = None  # Computed from cards, e.g., "W,U,B,R,G"
    date_created: Optional[str] = None
    date_modified: Optional[str] = None
    id: Optional[int] = None
    
    # Cube-specific properties
    archetypes: List[str] = field(default_factory=list)  # Supported archetypes
    themes: List[str] = field(default_factory=list)  # Cube themes (e.g., "graveyard", "artifacts")
    power_level: str = "high"  # high, medium, low
    complexity: str = "medium"  # high, medium, low
    is_singleton: bool = True  # Each card appears only once (except basic lands)
    is_peasant: bool = False  # Only common and uncommon cards allowed
    
    # Draft simulation data
    last_draft_date: Optional[str] = None
    draft_count: int = 0
    
    # Format-specific rules for cubes
    CUBE_FORMAT_RULES = {
        'vintage': {'min_cards': 180, 'max_cards': 1000, 'max_copies': 1, 'basic_lands': 'unlimited'},
        'legacy': {'min_cards': 180, 'max_cards': 1000, 'max_copies': 1, 'basic_lands': 'unlimited'},
        'modern': {'min_cards': 180, 'max_cards': 1000, 'max_copies': 1, 'basic_lands': 'unlimited'},
        'standard': {'min_cards': 180, 'max_cards': 1000, 'max_copies': 1, 'basic_lands': 'unlimited'},
        'pauper': {'min_cards': 180, 'max_cards': 1000, 'max_copies': 1, 'basic_lands': 'unlimited'},
    }
    
    def __post_init__(self):
        """Initialize timestamps if not set."""
        if self.date_created is None:
            self.date_created = datetime.now().isoformat()
        if self.date_modified is None:
            self.date_modified = self.date_created
    
    def get_non_land_cards(self) -> List[CubeCard]:
        """Get all non-land cards."""
        return [cc for cc in self.cards if not cc.card.is_land()]
    
    def get_land_cards(self) -> List[CubeCard]:
        """Get all land cards."""
        return [cc for cc in self.cards if cc.card.is_land()]
    
    def get_basic_lands(self) -> List[CubeCard]:
        """Get all basic land cards."""
        return [cc for cc in self.cards if cc.is_basic_land]
    
    def get_non_basic_lands(self) -> List[CubeCard]:
        """Get all non-basic land cards."""
        return [cc for cc in self.cards if cc.card.is_land() and not cc.is_basic_land]
    
    def get_cards_by_color(self, color: str) -> List[CubeCard]:
        """Get all cards that include the specified color."""
        return [cc for cc in self.cards if color in (cc.card.get_color_identity_list() or [])]
    
    def get_cards_by_type(self, card_type: str) -> List[CubeCard]:
        """Get all cards of a specific type."""
        return [cc for cc in self.cards if card_type.lower() in (cc.card.type_line or '').lower()]
    
    def get_cards_by_archetype(self, archetype: str) -> List[CubeCard]:
        """Get cards that support a specific archetype."""
        # This would need to be implemented based on card analysis
        # For now, return empty list
        return []
    
    def get_cards_by_cmc(self, cmc: int) -> List[CubeCard]:
        """Get all cards with a specific converted mana cost."""
        return [cc for cc in self.cards if cc.card.cmc == cmc]
    
    def get_cards_by_rarity(self, rarity: str) -> List[CubeCard]:
        """Get all cards of a specific rarity."""
        return [cc for cc in self.cards if cc.card.rarity and cc.card.rarity.lower() == rarity.lower()]
    
    def add_card(self, card: Card, quantity: int = 1, is_basic_land: bool = False, notes: str = None):
        """Add a card to the cube."""
        # Check singleton rule
        if self.is_singleton and not is_basic_land:
            for cc in self.cards:
                if cc.card.id == card.id:
                    # Card already exists, don't add more
                    return
        
        # Check peasant rule
        if self.is_peasant and card.rarity and card.rarity.lower() not in ['common', 'uncommon']:
            # Don't add non-peasant cards
            return
        
        # Check if card already exists
        for cc in self.cards:
            if cc.card.id == card.id:
                if self.is_singleton and not is_basic_land:
                    # Don't add more copies in singleton mode
                    return
                cc.quantity += quantity
                if notes:
                    cc.cube_notes = notes
                self.update_colors()
                self.date_modified = datetime.now().isoformat()
                return
        
        # Add new card
        cube_card = CubeCard(
            card=card,
            quantity=quantity,
            is_basic_land=is_basic_land,
            cube_notes=notes
        )
        self.cards.append(cube_card)
        self.update_colors()
        self.date_modified = datetime.now().isoformat()
    
    def remove_card(self, card: Card, quantity: int = 1):
        """Remove a card from the cube."""
        for i, cc in enumerate(self.cards):
            if cc.card.id == card.id:
                if cc.quantity <= quantity:
                    self.cards.pop(i)
                else:
                    cc.quantity -= quantity
                self.update_colors()
                self.date_modified = datetime.now().isoformat()
                return
    
    def update_colors(self):
        """Update the cube's color identity based on its cards."""
        color_set = set()
        for cc in self.cards:
            card_colors = cc.card.get_color_identity_list()
            if card_colors:
                color_set.update(card_colors)
        
        if color_set:
            self.colors = ','.join(sorted(color_set))
        else:
            self.colors = None
    
    def get_total_cards(self) -> int:
        """Get total number of cards in the cube."""
        return sum(cc.quantity for cc in self.cards)
    
    def get_card_count_by_type(self) -> Dict[str, int]:
        """Get count of cards by type."""
        type_counts = {}
        for cc in self.cards:
            if cc.card.type_line:
                # Get primary type (before the dash)
                primary_type = cc.card.type_line.split(' —')[0].strip()
                type_counts[primary_type] = type_counts.get(primary_type, 0) + cc.quantity
        return type_counts
    
    def get_color_distribution(self) -> Dict[str, int]:
        """Get distribution of cards by color."""
        color_counts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}
        for cc in self.cards:
            card_colors = cc.card.get_color_identity_list()
            if not card_colors:
                color_counts['C'] += cc.quantity
            else:
                for color in card_colors:
                    if color in color_counts:
                        color_counts[color] += cc.quantity
        return color_counts
    
    def get_mana_curve(self) -> Dict[int, int]:
        """Get the cube's mana curve."""
        curve = {}
        for cc in self.cards:
            if not cc.card.is_land():
                cmc = int(cc.card.cmc) if cc.card.cmc is not None else 0
                curve[cmc] = curve.get(cmc, 0) + cc.quantity
        return curve
    
    def validate_cube(self) -> Dict[str, List[str]]:
        """Validate the cube and return any issues."""
        issues = {
            'errors': [],
            'warnings': [],
            'info': []
        }
        
        # Check minimum size
        total_cards = self.get_total_cards()
        min_cards = self.CUBE_FORMAT_RULES.get(self.format, {}).get('min_cards', 180)
        if total_cards < min_cards:
            issues['errors'].append(f"Cube has {total_cards} cards, minimum is {min_cards}")
        
        # Check for basic lands
        basic_lands = self.get_basic_lands()
        if not basic_lands:
            issues['warnings'].append("No basic lands found - consider adding some")
        
        # Check color distribution
        color_dist = self.get_color_distribution()
        total_colored = sum(count for color, count in color_dist.items() if color != 'C')
        if total_colored > 0:
            for color, count in color_dist.items():
                if color != 'C':
                    percentage = (count / total_colored) * 100
                    if percentage < 10:
                        issues['warnings'].append(f"Low {color} representation: {percentage:.1f}%")
                    elif percentage > 30:
                        issues['warnings'].append(f"High {color} representation: {percentage:.1f}%")
        
        # Check for duplicate non-basic cards (singleton rule)
        if self.is_singleton:
            seen_cards = set()
            for cc in self.cards:
                if not cc.is_basic_land and cc.card.id in seen_cards:
                    issues['errors'].append(f"Duplicate non-basic card (singleton rule): {cc.card.name}")
                seen_cards.add(cc.card.id)
        
        # Check peasant rule (only common and uncommon cards)
        if self.is_peasant:
            for cc in self.cards:
                if cc.card.rarity and cc.card.rarity.lower() not in ['common', 'uncommon']:
                    issues['errors'].append(f"Non-peasant card: {cc.card.name} ({cc.card.rarity})")
        
        # Check for duplicate non-basic cards (general rule if not singleton)
        if not self.is_singleton:
            seen_cards = {}
            for cc in self.cards:
                if not cc.is_basic_land:
                    if cc.card.id in seen_cards:
                        seen_cards[cc.card.id] += cc.quantity
                    else:
                        seen_cards[cc.card.id] = cc.quantity
            
            # Warn about high duplicate counts
            for card_id, count in seen_cards.items():
                if count > 3:
                    card_name = next(cc.card.name for cc in self.cards if cc.card.id == card_id)
                    issues['warnings'].append(f"High duplicate count: {card_name} ({count} copies)")
        
        return issues
    
    def export_to_list(self) -> str:
        """Export cube to a text list format."""
        lines = [f"Cube: {self.name}", f"Size: {self.get_total_cards()}", ""]
        
        # Group by type
        type_groups = {}
        for cc in self.cards:
            if cc.card.type_line:
                primary_type = cc.card.type_line.split(' —')[0].strip()
                if primary_type not in type_groups:
                    type_groups[primary_type] = []
                type_groups[primary_type].append(cc)
        
        # Sort types
        type_order = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']
        for card_type in type_order:
            if card_type in type_groups:
                lines.append(f"{card_type}s:")
                cards = sorted(type_groups[card_type], key=lambda cc: cc.card.name)
                for cc in cards:
                    if cc.quantity > 1:
                        lines.append(f"  {cc.quantity}x {cc.card.name}")
                    else:
                        lines.append(f"  {cc.card.name}")
                lines.append("")
        
        return "\n".join(lines)
    
    def import_from_list(self, cube_list: str):
        """Import cube from a text list format."""
        # This would parse a text list and add cards
        # Implementation would depend on the specific format
        pass
