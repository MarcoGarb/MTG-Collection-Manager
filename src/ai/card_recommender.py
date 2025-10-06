"""
Card recommendation engine using unified deck analyzer.
"""
from typing import List, Dict, Tuple
from collections import Counter
import re
from src.models.card import Card
from src.models.deck import Deck
from src.ai.deck_analyzer import DeckAnalyzer


class CardRecommender:
    """Recommends cards based on deck composition and strategy."""
    
    # Format staples (unchanged)
    FORMAT_STAPLES = {
        'standard': {
            'removal': ['Hero\'s Downfall', 'Go for the Throat', 'Abrade', 'Destroy Evil'],
            'card_draw': ['Deep Analysis', 'Read the Bones', 'Sign in Blood'],
            'counterspells': ['Cancel', 'Negate', 'Essence Scatter'],
            'board_wipes': ['Wrath of God', 'Day of Judgment', 'Damnation'],
        },
        'commander': {
            'ramp': ['Sol Ring', 'Arcane Signet', 'Cultivate', 'Kodama\'s Reach', 'Rampant Growth'],
            'card_draw': ['Rhystic Study', 'Mystic Remora', 'Phyrexian Arena', 'Fact or Fiction'],
            'removal': ['Swords to Plowshares', 'Path to Exile', 'Beast Within', 'Generous Gift'],
            'board_wipes': ['Wrath of God', 'Blasphemous Act', 'Cyclonic Rift'],
        },
        'modern': {
            'removal': ['Fatal Push', 'Path to Exile', 'Lightning Bolt', 'Terminate'],
            'card_draw': ['Opt', 'Consider', 'Thought Scour'],
            'counterspells': ['Counterspell', 'Mana Leak', 'Force of Negation'],
        },
        'pauper': {
            'removal': ['Lightning Bolt', 'Galvanic Blast', 'Terminate', 'Doom Blade'],
            'card_draw': ['Preordain', 'Ponder', 'Deep Analysis'],
            'counterspells': ['Counterspell', 'Exclude', 'Prohibit'],
        }
    }
    
    def __init__(self, deck: Deck, collection: List[Card]):
        self.deck = deck
        self.collection = collection
        self.deck_cards = {dc.card.id for dc in deck.cards}
        self.available_cards = [c for c in collection if c.id not in self.deck_cards]
        
        # Use unified analyzer
        self.analyzer = DeckAnalyzer(deck)
        self.analysis = self.analyzer.analyze_deck()
    
    def get_recommendations(self, max_recommendations: int = 20) -> Dict[str, List[Tuple[Card, str, float]]]:
        """Get card recommendations organized by category."""
        recommendations = {
            'synergy': self._find_synergy_cards(),
            'curve': self._find_curve_fillers(),
            'removal': self._find_removal_cards(),
            'draw': self._find_card_draw(),
            'ramp': self._find_ramp_cards(),
            'lands': self._find_land_recommendations(),
            'staples': self._find_format_staples()
        }
        
        # Limit each category
        for category in recommendations:
            recommendations[category] = recommendations[category][:max_recommendations]
        
        return recommendations
    
    def _find_synergy_cards(self) -> List[Tuple[Card, str, float]]:
        """Find cards that synergize with existing deck cards."""
        recommendations = []
        
        deck_types = self.analysis['card_types']
        deck_keywords = self.analysis['keywords']
        deck_colors = self.analysis['colors']
        deck_themes = self.analysis['themes']
        
        for card in self.available_cards:
            score = 0.0
            reasons = []
            
            # Check color match
            card_colors = set(card.get_colors_list())
            if card_colors and card_colors.issubset(deck_colors):
                score += 2.0
            elif not card_colors:  # Colorless
                score += 1.0
            elif card_colors.intersection(deck_colors):
                score += 0.5
            else:
                continue
            
            text = (card.oracle_text or '').lower()
            type_line = (card.type_line or '').lower()
            
            # Tribal synergy
            for tribe in self.analyzer.TRIBES:
                if deck_types.get(tribe, 0) >= 3 and tribe in type_line:
                    score += 5.0
                    reasons.append(f"Tribal synergy ({tribe})")
                    break
            
            # Keyword synergy
            for keyword in deck_keywords:
                if keyword in text:
                    score += 2.0
                    reasons.append(f"Shares '{keyword}' keyword")
            
            # Theme synergy
            for theme, count in deck_themes.items():
                if count >= 3:
                    # Check if card supports this theme
                    theme_base = theme.replace('tribal_', '')
                    if any(kw in text for kw in self.analyzer.SYNERGY_KEYWORDS.get(theme_base, [])):
                        score += 3.0
                        reasons.append(f"{theme_base.capitalize()} synergy")
            
            if score > 2.0 and reasons:
                reason_text = ", ".join(reasons[:2])  # Limit reasons
                recommendations.append((card, reason_text, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_curve_fillers(self) -> List[Tuple[Card, str, float]]:
        """Find cards to improve mana curve."""
        recommendations = []
        curve = self.analysis['mana_curve']
        deck_colors = self.analysis['colors']
        
        # Find weak spots in curve
        weak_cmcs = [cmc for cmc in range(1, 5) if curve.get(cmc, 0) < 4]
        
        if not weak_cmcs:
            return recommendations
        
        for card in self.available_cards:
            if card.cmc not in weak_cmcs or card.is_land():
                continue
            
            card_colors = set(card.get_colors_list())
            if card_colors and not card_colors.issubset(deck_colors):
                continue
            
            score = 5.0
            if card.is_creature():
                score += 2.0
                reason = f"Creature at CMC {int(card.cmc)} (curve filler)"
            elif card.is_instant_or_sorcery():
                score += 1.5
                reason = f"Spell at CMC {int(card.cmc)} (curve filler)"
            else:
                score += 1.0
                reason = f"Card at CMC {int(card.cmc)} (curve filler)"
            
            recommendations.append((card, reason, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_removal_cards(self) -> List[Tuple[Card, str, float]]:
        """Find removal spells."""
        recommendations = []
        deck_colors = self.analysis['colors']
        
        for card in self.available_cards:
            card_colors = set(card.get_colors_list())
            if card_colors and not card_colors.issubset(deck_colors):
                continue
            
            text = (card.oracle_text or '').lower()
            score = 0.0
            
            if any(phrase in text for phrase in ['destroy all', 'exile all']):
                score = 8.0
                reason = "Board wipe"
            elif any(phrase in text for phrase in [
                'destroy target creature', 'exile target creature',
                'damage to target creature', 'damage to any target'
            ]):
                score = 7.0
                reason = "Creature removal"
            elif 'counter target' in text:
                score = 7.0
                reason = "Counterspell"
            elif any(phrase in text for phrase in ['destroy target', 'exile target']):
                score = 6.0
                reason = "Flexible removal"
            
            if score > 0:
                recommendations.append((card, reason, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_card_draw(self) -> List[Tuple[Card, str, float]]:
        """Find card draw spells."""
        recommendations = []
        deck_colors = self.analysis['colors']
        
        for card in self.available_cards:
            card_colors = set(card.get_colors_list())
            if card_colors and not card_colors.issubset(deck_colors):
                continue
            
            text = (card.oracle_text or '').lower()
            score = 0.0
            
            if 'draw' in text and 'card' in text and 'opponent' not in text:
                draw_match = re.search(r'draw (\w+) card', text)
                if draw_match:
                    draw_count = draw_match.group(1)
                    if draw_count in ['two', '2', 'three', '3']:
                        score = 8.0
                    else:
                        score = 7.0
                else:
                    score = 6.0
                reason = "Card draw"
            elif any(kw in text for kw in ['scry', 'surveil']):
                score = 5.0
                reason = "Card selection"
            
            if score > 0:
                recommendations.append((card, reason, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_ramp_cards(self) -> List[Tuple[Card, str, float]]:
        """Find mana ramp cards."""
        recommendations = []
        deck_colors = self.analysis['colors']
        
        for card in self.available_cards:
            card_colors = set(card.get_colors_list())
            if card_colors and not card_colors.issubset(deck_colors):
                continue
            
            text = (card.oracle_text or '').lower()
            score = 0.0
            
            if 'add' in text and ('{t}' in text or 'tap' in text):
                score = 7.0
                reason = "Mana rock"
            elif 'search your library' in text and 'land' in text:
                score = 8.0
                reason = "Land ramp"
            elif card.is_creature() and 'add' in text:
                score = 6.0
                reason = "Mana dork"
            
            if score > 0:
                recommendations.append((card, reason, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_land_recommendations(self) -> List[Tuple[Card, str, float]]:
        """Find good lands for the deck."""
        recommendations = []
        deck_colors = self.analysis['colors']
        
        if not deck_colors:
            return recommendations
        
        for card in self.available_cards:
            if not card.is_land():
                continue
            
            text = (card.oracle_text or '').lower()
            type_line = (card.type_line or '').lower()
            
            if 'basic' in type_line:
                continue
            
            score = 0.0
            reason = None
            
            # Check if land produces deck colors
            produces_colors = [color for color in deck_colors if f'{color.lower()}' in text]
            
            if len(produces_colors) >= 2:
                score = 8.0
                reason = f"Dual land ({'/'.join(produces_colors)})"
            elif len(produces_colors) == 1:
                score = 6.0
                reason = f"Produces {produces_colors[0]}"
            
            # Utility lands
            if any(kw in text for kw in ['draw', 'sacrifice', 'create']):
                if reason:
                    score += 2.0
                    reason += " + utility"
                else:
                    score = 5.0
                    reason = "Utility land"
            
            if score > 0 and reason:
                recommendations.append((card, reason, score))
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations
    
    def _find_format_staples(self) -> List[Tuple[Card, str, float]]:
        """Find format staples that aren't in the deck."""
        recommendations = []
        deck_format = self.deck.format
        deck_colors = self.analysis['colors']
        
        if deck_format not in self.FORMAT_STAPLES:
            return recommendations
        
        staples = self.FORMAT_STAPLES[deck_format]
        all_staples = [(card_name, category) for category, cards in staples.items() for card_name in cards]
        
        for card in self.available_cards:
            for staple_name, category in all_staples:
                if card.name.lower() == staple_name.lower():
                    card_colors = set(card.get_colors_list())
                    if card_colors and not card_colors.issubset(deck_colors):
                        continue
                    
                    score = 9.0
                    reason = f"Format staple ({category})"
                    recommendations.append((card, reason, score))
                    break
        
        recommendations.sort(key=lambda x: -x[2])
        return recommendations