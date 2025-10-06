"""
Unified deck analysis engine.
Used by deck insights, recommendations, and AI deck builder.
"""
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from src.models.deck import Deck, DeckCard
from src.models.card import Card
import re


class DeckAnalyzer:
    """Comprehensive deck analysis for manual and AI deck building."""
    
    # Synergy keywords
    SYNERGY_KEYWORDS = {
        'graveyard': ['graveyard', 'from your graveyard', 'return', 'mill', 'flashback', 'delve', 'disturb'],
        'artifacts': ['artifact', 'equipment', 'thopter', 'construct', 'affinity'],
        'tokens': ['create', 'token', 'populate', 'convoke'],
        'sacrifice': ['sacrifice', 'dies', 'when .* dies', 'aristocrat'],
        'lifegain': ['gain', 'life', 'lifelink', 'when you gain life'],
        'counters': ['+1/+1 counter', 'proliferate', 'counter on'],
        'spells': ['instant', 'sorcery', 'prowess', 'whenever you cast'],
    }
    
    # Keyword abilities
    KEYWORD_ABILITIES = [
        'flying', 'trample', 'haste', 'vigilance', 'lifelink', 'deathtouch',
        'first strike', 'double strike', 'menace', 'hexproof', 'indestructible',
        'flash', 'defender', 'reach', 'prowess', 'convoke', 'affinity'
    ]
    
    # Tribes
    TRIBES = [
        'zombie', 'goblin', 'elf', 'vampire', 'human', 'dragon', 
        'wizard', 'knight', 'soldier', 'merfolk', 'angel', 'demon'
    ]
    
    def __init__(self, deck: Deck = None):
        self.deck = deck
    
    # ============================================================
    # CARD FINDING METHODS (Shared Logic)
    # ============================================================
    
    def find_card_draw(self, cards: List[DeckCard]) -> List[DeckCard]:
        """Find cards that draw cards."""
        draw_keywords = ['draw', 'draws', 'scry', 'surveil', 'investigate', 'conjure', 'discover', 'explore']
        draw_cards = []
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            
            # Check for draw keywords
            if any(keyword in text for keyword in draw_keywords):
                # Exclude "opponent draws" effects
                if 'opponent' not in text or text.count('draw') > text.count('opponent'):
                    draw_cards.append(dc)
                    continue
            
            # Planeswalkers often provide card advantage
            if dc.card.type_line and 'Planeswalker' in dc.card.type_line:
                draw_cards.append(dc)
        
        return draw_cards
    
    def find_removal(self, cards: List[DeckCard]) -> Dict[str, List[DeckCard]]:
        """Find removal and interaction spells."""
        removal_types = {
            'creature_removal': [],
            'board_wipes': [],
            'counterspells': [],
            'discard': [],
            'other': []
        }
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            
            # Counterspells
            if 'counter target' in text or 'counter that' in text:
                removal_types['counterspells'].append(dc)
            # Board wipes
            elif any(phrase in text for phrase in ['destroy all', 'exile all', '-X/-X', 'damage to each']):
                removal_types['board_wipes'].append(dc)
            # Discard
            elif 'discard' in text and 'opponent' in text:
                removal_types['discard'].append(dc)
            # Creature removal
            elif any(phrase in text for phrase in [
                'destroy target creature', 'exile target creature',
                'target creature gets', 'damage to target creature',
                'damage to any target', 'return target creature'
            ]):
                removal_types['creature_removal'].append(dc)
            # Other removal
            elif any(phrase in text for phrase in ['destroy target', 'exile target', 'return target']):
                removal_types['other'].append(dc)
        
        return removal_types
    
    def find_ramp(self, cards: List[DeckCard]) -> List[DeckCard]:
        """Find mana acceleration cards."""
        ramp_cards = []
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            type_line = (dc.card.type_line or '').lower()
            
            # Mana rocks and dorks
            if 'add' in text and any(symbol in text for symbol in ['{', 'mana']):
                # Exclude basic lands
                if 'basic' not in type_line or 'land' not in type_line:
                    ramp_cards.append(dc)
            # Search for lands
            elif 'search your library' in text and 'land' in text:
                ramp_cards.append(dc)
            # Put lands onto battlefield
            elif 'put' in text and 'land' in text and 'onto the battlefield' in text:
                ramp_cards.append(dc)
        
        return ramp_cards
    
    def find_threats(self, cards: List[DeckCard]) -> List[DeckCard]:
        """Find cards that are threats (win the game)."""
        threats = []
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            
            # Creatures are usually threats
            if dc.card.is_creature():
                threats.append(dc)
            # Planeswalkers are threats
            elif 'Planeswalker' in (dc.card.type_line or ''):
                threats.append(dc)
            # Cards that create tokens
            elif 'create' in text and 'token' in text:
                threats.append(dc)
            # Cards with attack/combat keywords
            elif any(kw in text for kw in ['combat', 'attack', 'damage to opponent']):
                threats.append(dc)
        
        return threats
    
    def find_answers(self, cards: List[DeckCard]) -> List[DeckCard]:
        """Find cards that answer threats."""
        answers = []
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            
            # Any removal is an answer
            if any(phrase in text for phrase in ['destroy', 'exile', 'counter', 'return', 'damage', 'gets -']):
                answers.append(dc)
            # Protection/defensive cards
            elif any(kw in text for kw in ['prevent', 'protection', 'indestructible', 'hexproof']):
                answers.append(dc)
        
        return answers
    
    # ============================================================
    # THEME DETECTION
    # ============================================================
    
    def detect_themes(self, cards: List[DeckCard]) -> Dict[str, int]:
        """Detect deck themes and synergies."""
        themes = defaultdict(int)
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            type_line = (dc.card.type_line or '').lower()
            
            # Check synergy keywords
            for theme_name, keywords in self.SYNERGY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        themes[theme_name] += dc.quantity
                        break
            
            # Check for tribal themes
            for tribe in self.TRIBES:
                if tribe in type_line:
                    themes[f'tribal_{tribe}'] += dc.quantity
        
        return dict(themes)
    
    def has_theme(self, cards: List[DeckCard], theme: str, threshold: int = 3) -> bool:
        """Check if deck has a specific theme (threshold cards)."""
        themes = self.detect_themes(cards)
        return themes.get(theme, 0) >= threshold
    
    # ============================================================
    # DECK TYPE EXTRACTION
    # ============================================================
    
    def get_deck_card_types(self, cards: List[DeckCard]) -> Counter:
        """Get counter of card types and subtypes in deck."""
        types = Counter()
        
        for dc in cards:
            type_line = (dc.card.type_line or '').lower()
            
            # Add main types
            for t in ['creature', 'instant', 'sorcery', 'enchantment', 'artifact', 'planeswalker']:
                if t in type_line:
                    types[t] += dc.quantity
            
            # Add subtypes
            if '-' in type_line or '\u2014' in type_line:  # \u2014 is em dash
                # Split on both hyphen and em dash
                parts = re.split(r'[-\u2014]', type_line)
   
                if len(parts) > 1:
                    subtypes = parts[-1].strip()
                    for subtype in subtypes.split():
                        types[subtype] += dc.quantity
        
        return types
    
    def get_deck_keywords(self, cards: List[DeckCard]) -> Set[str]:
        """Get set of keyword abilities used in deck."""
        keywords = set()
        
        for dc in cards:
            text = (dc.card.oracle_text or '').lower()
            type_line = (dc.card.type_line or '').lower()
            
            for keyword in self.KEYWORD_ABILITIES:
                if keyword in text or keyword in type_line:
                    keywords.add(keyword)
        
        return keywords
    
    # ============================================================
    # COMPREHENSIVE ANALYSIS
    # ============================================================
    
    def analyze_deck(self, deck: Deck = None) -> Dict:
        """
        Comprehensive deck analysis.
        Returns dict with all analysis results.
        """
        if deck:
            self.deck = deck
        
        if not self.deck:
            raise ValueError("No deck provided for analysis")
        
        mainboard = self.deck.get_mainboard_cards()
        
        # Find card categories
        card_draw = self.find_card_draw(mainboard)
        removal = self.find_removal(mainboard)
        ramp = self.find_ramp(mainboard)
        threats = self.find_threats(mainboard)
        answers = self.find_answers(mainboard)
        
        # Detect themes
        themes = self.detect_themes(mainboard)
        card_types = self.get_deck_card_types(mainboard)
        keywords = self.get_deck_keywords(mainboard)
        
        # Calculate counts
        total_removal = sum(sum(dc.quantity for dc in cards) for cards in removal.values())
        
        return {
            'card_draw': card_draw,
            'card_draw_count': sum(dc.quantity for dc in card_draw),
            'removal': removal,
            'removal_count': total_removal,
            'ramp': ramp,
            'ramp_count': sum(dc.quantity for dc in ramp),
            'threats': threats,
            'threats_count': sum(dc.quantity for dc in threats),
            'answers': answers,
            'answers_count': sum(dc.quantity for dc in answers),
            'themes': themes,
            'card_types': card_types,
            'keywords': keywords,
            'mana_curve': self.deck.get_mana_curve(),
            'colors': set(self.deck.get_colors()),
        }