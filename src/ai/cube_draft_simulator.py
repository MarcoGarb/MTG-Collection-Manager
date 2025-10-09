"""
Cube Draft Simulator - Simulate drafting from a cube.
"""
import random
from typing import List, Dict, Optional, Tuple
from src.models.cube import Cube, CubeCard
from src.models.card import Card
from src.models.deck import Deck, DeckCard
from src.ai.deck_analyzer import DeckAnalyzer

class DraftPlayer:
    """Represents a player in a cube draft."""
    
    def __init__(self, name: str, strategy: str = "balanced"):
        self.name = name
        self.strategy = strategy  # "aggro", "control", "midrange", "combo", "balanced"
        self.pool = []  # Cards drafted
        self.picks = []  # Pick history for analysis
        self.deck = None  # Final constructed deck
    
    def add_card(self, card: Card, pick_number: int, pack_number: int):
        """Add a card to the player's pool."""
        self.pool.append(card)
        self.picks.append({
            'card': card,
            'pick_number': pick_number,
            'pack_number': pack_number,
            'pack_position': 0  # Will be set by simulator
        })
    
    def build_deck(self, cube: Cube) -> Deck:
        """Build a deck from the drafted pool."""
        if not self.pool:
            return Deck(name=f"{self.name}'s Deck", format="vintage")
        
        # Analyze the pool to determine colors
        colors = self._determine_colors()
        
        # Create deck
        deck = Deck(
            name=f"{self.name}'s Draft Deck",
            format=cube.format,
            description=f"Drafted from {cube.name}"
        )
        
        # Add cards to deck (simplified - just add all drafted cards)
        for card in self.pool:
            deck.add_card(card, quantity=1)
        
        # Add basic lands
        self._add_basic_lands(deck, colors)
        
        self.deck = deck
        return deck
    
    def _determine_colors(self) -> List[str]:
        """Determine the main colors from the drafted pool."""
        color_counts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}
        
        for card in self.pool:
            card_colors = card.get_color_identity_list()
            if card_colors:
                for color in card_colors:
                    if color in color_counts:
                        color_counts[color] += 1
        
        # Return top 2 colors
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        return [color for color, count in sorted_colors[:2] if count > 0]
    
    def _add_basic_lands(self, deck: Deck, colors: List[str]):
        """Add basic lands to the deck."""
        if not colors:
            colors = ['C']
        
        # Add 17-18 lands (typical for 40-card draft deck)
        land_count = 17
        per_color = land_count // len(colors)
        
        basic_land_names = {
            'W': 'Plains', 'U': 'Island', 'B': 'Swamp', 
            'R': 'Mountain', 'G': 'Forest', 'C': 'Wastes'
        }
        
        for color in colors:
            if color in basic_land_names:
                land_name = basic_land_names[color]
                # Create virtual basic land
                basic_land = Card(
                    id=-ord(land_name[0]),
                    name=land_name,
                    set_code='BASIC',
                    collector_number='0',
                    rarity='common',
                    mana_cost='',
                    cmc=0.0,
                    colors=color if color != 'C' else '',
                    color_identity=color if color != 'C' else '',
                    type_line=f'Basic Land — {land_name}',
                    card_types='Land,Basic',
                    subtypes=land_name,
                    oracle_text=f'({{T}}: Add {{{color}}}.)' if color != 'C' else '({T}: Add {C}.)',
                    quantity=999
                )
                deck.add_card(basic_land, quantity=per_color)

class CubeDraftSimulator:
    """Simulates drafting from a cube."""
    
    def __init__(self, cube: Cube):
        self.cube = cube
        self.players = []
        self.packs = []
        self.draft_log = []
    
    def add_player(self, name: str, strategy: str = "balanced"):
        """Add a player to the draft."""
        self.players.append(DraftPlayer(name, strategy))
    
    def create_packs(self, cards_per_pack: int = 15, num_packs: int = 3):
        """Create packs for drafting."""
        # Get all non-basic land cards from the cube
        draftable_cards = [cc.card for cc in self.cube.cards if not cc.is_basic_land]
        
        if len(draftable_cards) < cards_per_pack * num_packs * len(self.players):
            raise ValueError("Not enough cards in cube for this draft configuration")
        
        # Shuffle and create packs
        random.shuffle(draftable_cards)
        
        self.packs = []
        card_index = 0
        
        for pack_num in range(num_packs):
            for player_num in range(len(self.players)):
                pack = []
                for _ in range(cards_per_pack):
                    if card_index < len(draftable_cards):
                        pack.append(draftable_cards[card_index])
                        card_index += 1
                self.packs.append(pack)
        
        self.draft_log.append(f"Created {len(self.packs)} packs with {cards_per_pack} cards each")
    
    def simulate_draft(self, draft_type: str = "winston") -> List[Deck]:
        """Simulate a draft and return the constructed decks."""
        if not self.players:
            raise ValueError("No players added to draft")
        
        if not self.packs:
            self.create_packs()
        
        if draft_type == "winston":
            return self._simulate_winston_draft()
        elif draft_type == "grid":
            return self._simulate_grid_draft()
        else:
            return self._simulate_rotisserie_draft()
    
    def _simulate_winston_draft(self) -> List[Deck]:
        """Simulate a Winston draft."""
        # Winston draft: players take turns picking from face-down piles
        # This is a simplified version
        
        # Distribute packs to players
        packs_per_player = len(self.packs) // len(self.players)
        
        for i, player in enumerate(self.players):
            start_idx = i * packs_per_player
            end_idx = start_idx + packs_per_player
            player_packs = self.packs[start_idx:end_idx]
            
            # Draft from packs
            for pack in player_packs:
                random.shuffle(pack)
                for card in pack:
                    # Simple AI: pick cards that match strategy
                    if self._should_pick_card(card, player):
                        player.add_card(card, len(player.pool) + 1, 1)
                        break
        
        # Build decks
        decks = []
        for player in self.players:
            deck = player.build_deck(self.cube)
            decks.append(deck)
        
        return decks
    
    def _simulate_grid_draft(self) -> List[Deck]:
        """Simulate a grid draft (2 players)."""
        if len(self.players) != 2:
            raise ValueError("Grid draft requires exactly 2 players")
        
        # Grid draft: 3x3 grid of cards, players take rows or columns
        # This is a simplified version
        
        # Use all packs for grid draft
        all_cards = []
        for pack in self.packs:
            all_cards.extend(pack)
        
        random.shuffle(all_cards)
        
        # Create 3x3 grids
        grid_size = 9
        num_grids = len(all_cards) // grid_size
        
        for grid_num in range(num_grids):
            start_idx = grid_num * grid_size
            grid_cards = all_cards[start_idx:start_idx + grid_size]
            
            # Players alternate picking rows or columns
            for turn in range(2):  # 2 picks per grid
                player = self.players[turn % 2]
                
                # Simple AI: pick the best card
                best_card = self._get_best_card_for_player(grid_cards, player)
                if best_card:
                    player.add_card(best_card, len(player.pool) + 1, grid_num + 1)
                    grid_cards.remove(best_card)
        
        # Build decks
        decks = []
        for player in self.players:
            deck = player.build_deck(self.cube)
            decks.append(deck)
        
        return decks
    
    def _simulate_rotisserie_draft(self) -> List[Deck]:
        """Simulate a rotisserie draft (snake draft)."""
        # Rotisserie: all cards visible, players take turns picking
        
        # Get all cards
        all_cards = []
        for pack in self.packs:
            all_cards.extend(pack)
        
        # Remove duplicates and sort by power level (simplified)
        unique_cards = list(set(all_cards))
        unique_cards.sort(key=lambda c: self._get_card_power_level(c), reverse=True)
        
        # Snake draft
        pick_order = list(range(len(self.players)))
        pick_order.extend(reversed(pick_order))  # Snake back
        
        for i, card in enumerate(unique_cards):
            if i >= len(self.players) * 45:  # Limit picks
                break
            
            player_idx = pick_order[i % len(pick_order)]
            player = self.players[player_idx]
            
            if self._should_pick_card(card, player):
                player.add_card(card, len(player.pool) + 1, 1)
        
        # Build decks
        decks = []
        for player in self.players:
            deck = player.build_deck(self.cube)
            decks.append(deck)
        
        return decks
    
    def _should_pick_card(self, card: Card, player: DraftPlayer) -> bool:
        """Determine if a player should pick a card based on their strategy."""
        # Simple AI based on strategy
        if player.strategy == "aggro":
            return self._is_aggro_card(card)
        elif player.strategy == "control":
            return self._is_control_card(card)
        elif player.strategy == "combo":
            return self._is_combo_card(card)
        else:  # balanced
            return True
    
    def _is_aggro_card(self, card: Card) -> bool:
        """Check if a card is good for aggro."""
        if not card.type_line:
            return False
        
        # Creatures with low CMC
        if 'Creature' in card.type_line and card.cmc and card.cmc <= 3:
            return True
        
        # Direct damage spells
        text = (card.oracle_text or '').lower()
        if 'damage' in text and card.cmc and card.cmc <= 3:
            return True
        
        return False
    
    def _is_control_card(self, card: Card) -> bool:
        """Check if a card is good for control."""
        if not card.type_line:
            return False
        
        # Counterspells
        text = (card.oracle_text or '').lower()
        if 'counter' in text and 'spell' in text:
            return True
        
        # Card draw
        if 'draw' in text:
            return True
        
        # Removal
        if any(word in text for word in ['destroy', 'exile', 'return to hand']):
            return True
        
        return False
    
    def _is_combo_card(self, card: Card) -> bool:
        """Check if a card is good for combo."""
        if not card.type_line:
            return False
        
        text = (card.oracle_text or '').lower()
        
        # Cards with triggers or activated abilities
        if any(word in text for word in ['when', 'whenever', 'activate', 'sacrifice']):
            return True
        
        # Mana acceleration
        if 'add' in text and 'mana' in text:
            return True
        
        return False
    
    def _get_best_card_for_player(self, cards: List[Card], player: DraftPlayer) -> Card:
        """Get the best card for a player from a list."""
        if not cards:
            return None
        
        # Simple scoring system
        best_card = None
        best_score = -1
        
        for card in cards:
            score = self._get_card_score(card, player)
            if score > best_score:
                best_score = score
                best_card = card
        
        return best_card
    
    def _get_card_score(self, card: Card, player: DraftPlayer) -> float:
        """Score a card for a player."""
        score = 0.0
        
        # Base power level
        score += self._get_card_power_level(card)
        
        # Strategy bonus
        if player.strategy == "aggro" and self._is_aggro_card(card):
            score += 2.0
        elif player.strategy == "control" and self._is_control_card(card):
            score += 2.0
        elif player.strategy == "combo" and self._is_combo_card(card):
            score += 2.0
        
        # CMC bonus (prefer lower CMC)
        if card.cmc is not None:
            score += max(0, 6 - card.cmc) * 0.5
        
        return score
    
    def _get_card_power_level(self, card: Card) -> float:
        """Get the power level of a card (0-10 scale)."""
        # Simple power level based on rarity
        rarity_scores = {
            'common': 2.0,
            'uncommon': 4.0,
            'rare': 6.0,
            'mythic': 8.0
        }
        
        base_score = rarity_scores.get(card.rarity, 1.0)
        
        # Bonus for low CMC
        if card.cmc is not None and card.cmc <= 2:
            base_score += 1.0
        
        return base_score
    
    def get_draft_analysis(self) -> Dict:
        """Get analysis of the draft."""
        analysis = {
            'total_players': len(self.players),
            'total_cards_drafted': sum(len(player.pool) for player in self.players),
            'average_cards_per_player': sum(len(player.pool) for player in self.players) / len(self.players),
            'players': []
        }
        
        for player in self.players:
            player_analysis = {
                'name': player.name,
                'strategy': player.strategy,
                'cards_drafted': len(player.pool),
                'colors': player._determine_colors(),
                'deck_quality': self._analyze_deck_quality(player.deck) if player.deck else 0
            }
            analysis['players'].append(player_analysis)
        
        return analysis
    
    def _analyze_deck_quality(self, deck: Deck) -> float:
        """Analyze the quality of a constructed deck."""
        if not deck:
            return 0.0
        
        try:
            analyzer = DeckAnalyzer(deck)
            analysis = analyzer.analyze_deck()
            
            # Simple quality score based on analysis
            quality = 0.0
            
            # Mana curve bonus
            curve = analysis.get('mana_curve', {})
            if curve:
                # Prefer a good curve distribution
                low_cmc = sum(curve.get(i, 0) for i in range(3))
                total_cards = sum(curve.values())
                if total_cards > 0:
                    curve_ratio = low_cmc / total_cards
                    quality += curve_ratio * 30
            
            # Color consistency bonus
            colors = analysis.get('colors', [])
            if len(colors) <= 2:
                quality += 20
            elif len(colors) == 3:
                quality += 10
            
            # Card type diversity bonus
            card_types = analysis.get('card_types', {})
            if len(card_types) >= 3:
                quality += 15
            
            return min(100, quality)
        except:
            return 0.0
