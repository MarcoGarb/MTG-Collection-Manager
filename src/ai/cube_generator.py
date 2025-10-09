"""
AI-powered cube generator using genetic algorithm and archetype analysis.
"""
import random
from typing import List, Optional, Dict, Tuple
from src.models.card import Card
from src.models.cube import Cube, CubeCard
from src.ai.deck_analyzer import DeckAnalyzer
from datetime import datetime
from dataclasses import dataclass

# Cube archetype templates
CUBE_ARCHETYPE_TEMPLATES = {
    'power_cube': {
        'size': 360,
        'power_level': 'high',
        'complexity': 'high',
        'color_distribution': {'W': 0.18, 'U': 0.18, 'B': 0.18, 'R': 0.18, 'G': 0.18, 'C': 0.10},
        'type_distribution': {'Creature': 0.40, 'Instant': 0.15, 'Sorcery': 0.10, 'Enchantment': 0.10, 'Artifact': 0.15, 'Planeswalker': 0.05, 'Land': 0.05},
        'mana_curve': {0: 0.05, 1: 0.10, 2: 0.20, 3: 0.25, 4: 0.20, 5: 0.15, 6: 0.05},
        'rarity_distribution': {'mythic': 0.05, 'rare': 0.20, 'uncommon': 0.35, 'common': 0.40},
        'themes': ['combo', 'control', 'aggro', 'midrange', 'ramp', 'graveyard', 'artifacts']
    },
    'vintage_cube': {
        'size': 450,
        'power_level': 'high',
        'complexity': 'high',
        'color_distribution': {'W': 0.18, 'U': 0.18, 'B': 0.18, 'R': 0.18, 'G': 0.18, 'C': 0.10},
        'type_distribution': {'Creature': 0.35, 'Instant': 0.15, 'Sorcery': 0.10, 'Enchantment': 0.10, 'Artifact': 0.20, 'Planeswalker': 0.05, 'Land': 0.05},
        'mana_curve': {0: 0.05, 1: 0.10, 2: 0.20, 3: 0.25, 4: 0.20, 5: 0.15, 6: 0.05},
        'rarity_distribution': {'mythic': 0.08, 'rare': 0.25, 'uncommon': 0.35, 'common': 0.32},
        'themes': ['combo', 'control', 'aggro', 'midrange', 'ramp', 'graveyard', 'artifacts', 'storm']
    },
    'legacy_cube': {
        'size': 360,
        'power_level': 'medium',
        'complexity': 'medium',
        'color_distribution': {'W': 0.20, 'U': 0.20, 'B': 0.20, 'R': 0.20, 'G': 0.20, 'C': 0.00},
        'type_distribution': {'Creature': 0.45, 'Instant': 0.15, 'Sorcery': 0.10, 'Enchantment': 0.10, 'Artifact': 0.15, 'Planeswalker': 0.05, 'Land': 0.00},
        'mana_curve': {0: 0.05, 1: 0.15, 2: 0.25, 3: 0.25, 4: 0.20, 5: 0.10, 6: 0.00},
        'rarity_distribution': {'mythic': 0.05, 'rare': 0.20, 'uncommon': 0.40, 'common': 0.35},
        'themes': ['aggro', 'midrange', 'control', 'combo', 'tribal']
    },
    'modern_cube': {
        'size': 360,
        'power_level': 'medium',
        'complexity': 'medium',
        'color_distribution': {'W': 0.20, 'U': 0.20, 'B': 0.20, 'R': 0.20, 'G': 0.20, 'C': 0.00},
        'type_distribution': {'Creature': 0.50, 'Instant': 0.15, 'Sorcery': 0.10, 'Enchantment': 0.10, 'Artifact': 0.10, 'Planeswalker': 0.05, 'Land': 0.00},
        'mana_curve': {0: 0.05, 1: 0.15, 2: 0.25, 3: 0.25, 4: 0.20, 5: 0.10, 6: 0.00},
        'rarity_distribution': {'mythic': 0.05, 'rare': 0.20, 'uncommon': 0.40, 'common': 0.35},
        'themes': ['aggro', 'midrange', 'control', 'tribal', 'artifacts']
    },
    'pauper_cube': {
        'size': 360,
        'power_level': 'low',
        'complexity': 'low',
        'color_distribution': {'W': 0.20, 'U': 0.20, 'B': 0.20, 'R': 0.20, 'G': 0.20, 'C': 0.00},
        'type_distribution': {'Creature': 0.50, 'Instant': 0.15, 'Sorcery': 0.15, 'Enchantment': 0.10, 'Artifact': 0.05, 'Planeswalker': 0.00, 'Land': 0.05},
        'mana_curve': {0: 0.05, 1: 0.20, 2: 0.30, 3: 0.25, 4: 0.15, 5: 0.05, 6: 0.00},
        'rarity_distribution': {'mythic': 0.00, 'rare': 0.00, 'uncommon': 0.30, 'common': 0.70},
        'themes': ['aggro', 'midrange', 'control', 'tribal']
    },
    'themed_cube': {
        'size': 360,
        'power_level': 'medium',
        'complexity': 'high',
        'color_distribution': {'W': 0.20, 'U': 0.20, 'B': 0.20, 'R': 0.20, 'G': 0.20, 'C': 0.00},
        'type_distribution': {'Creature': 0.45, 'Instant': 0.15, 'Sorcery': 0.10, 'Enchantment': 0.10, 'Artifact': 0.15, 'Planeswalker': 0.05, 'Land': 0.00},
        'mana_curve': {0: 0.05, 1: 0.15, 2: 0.25, 3: 0.25, 4: 0.20, 5: 0.10, 6: 0.00},
        'rarity_distribution': {'mythic': 0.05, 'rare': 0.20, 'uncommon': 0.40, 'common': 0.35},
        'themes': ['graveyard', 'artifacts', 'tribal', 'spells']  # Customizable themes
    }
}

class CubeGenerator:
    """Generate optimized cubes using genetic algorithm."""
    
    def __init__(self, collection: List[Card]):
        self.collection = collection
        self.analyzer = DeckAnalyzer()
    
    def generate_cube(
        self,
        cube_type: str = 'power_cube',
        target_size: int = 360,
        themes: List[str] = None,
        power_level: str = 'high',
        complexity: str = 'high',
        is_singleton: bool = True,
        is_peasant: bool = False,
        availability_ledger: Optional[Dict[int, int]] = None
    ) -> Cube:
        """Generate a cube using a genetic algorithm."""
        print(f"🔍 Starting cube generation: {cube_type}")
        
        # Validate cube type
        if cube_type not in CUBE_ARCHETYPE_TEMPLATES:
            raise ValueError(f"Unknown cube type: {cube_type}")
        
        template = CUBE_ARCHETYPE_TEMPLATES[cube_type]
        
        # Override template values with user preferences
        if target_size:
            template = template.copy()
            template['size'] = target_size
        if themes:
            template = template.copy()
            template['themes'] = themes
        if power_level:
            template = template.copy()
            template['power_level'] = power_level
        if complexity:
            template = template.copy()
            template['complexity'] = complexity
        
        # Filter collection by availability and peasant rule if provided
        valid_cards = self.collection
        if availability_ledger:
            valid_cards = [
                card for card in self.collection
                if availability_ledger.get(getattr(card, 'id', None), 0) > 0
            ]
            print(f"🔍 Filtered to {len(valid_cards)} available cards")
        
        # Filter by peasant rule
        if is_peasant:
            valid_cards = [
                card for card in valid_cards
                if not card.rarity or card.rarity.lower() in ['common', 'uncommon']
            ]
            print(f"🔍 Peasant filter: {len(valid_cards)} common/uncommon cards")
        
        if not valid_cards:
            raise ValueError("No cards available for cube generation")
        
        # Run genetic algorithm
        print("🧬 Running genetic algorithm...")
        best_cube = self._genetic_algorithm(
            valid_cards,
            template,
            is_singleton,
            is_peasant,
            availability_ledger
        )
        
        if best_cube is None:
            raise ValueError("Genetic algorithm returned None!")
        
        print(f"✅ Generated cube: {best_cube.name}")
        return best_cube
    
    def _genetic_algorithm(
        self,
        card_pool: List[Card],
        template: Dict,
        is_singleton: bool = True,
        is_peasant: bool = False,
        availability_ledger: Optional[Dict[int, int]] = None
    ) -> Cube:
        """Run genetic algorithm to generate optimal cube."""
        
        # GA parameters
        POPULATION_SIZE = 30
        GENERATIONS = 50
        MUTATION_RATE = 0.20
        ELITE_SIZE = 3
        
        # Initialize population
        population = [
            self._create_random_cube(card_pool, template, is_singleton, is_peasant, availability_ledger)
            for _ in range(POPULATION_SIZE)
        ]
        
        best_score = -float('inf')
        best_cube = population[0] if population else None
        
        for generation in range(GENERATIONS):
            # Evaluate fitness
            fitness_scores = [(cube, self._evaluate_cube(cube, template)) for cube in population]
            fitness_scores.sort(key=lambda x: -x[1])
            
            current_best_score = fitness_scores[0][1]
            
            if current_best_score > best_score:
                best_score = current_best_score
                best_cube = fitness_scores[0][0]
                print(f"Generation {generation}: Best score = {best_score:.2f}")
            
            # Selection: Keep elite
            new_population = [cube for cube, score in fitness_scores[:ELITE_SIZE]]
            
            # Crossover and mutation
            while len(new_population) < POPULATION_SIZE:
                parent1 = self._tournament_selection(fitness_scores, 5)
                parent2 = self._tournament_selection(fitness_scores, 5)
                
                child = self._crossover(parent1, parent2, card_pool, template, is_singleton, is_peasant)
                
                if random.random() < MUTATION_RATE:
                    child = self._mutate(child, card_pool, template, is_singleton, is_peasant)
                
                new_population.append(child)
            
            population = new_population
        
        return best_cube
    
    def _create_random_cube(
        self,
        card_pool: List[Card],
        template: Dict,
        is_singleton: bool = True,
        is_peasant: bool = False,
        availability_ledger: Optional[Dict[int, int]] = None
    ) -> Cube:
        """Create a random cube from card pool following template guidelines."""
        
        cube = Cube(
            name=f"{template['power_level'].title()} {template.get('themes', ['Cube'])[0].title()} Cube",
            size=template['size'],
            format=template.get('format', 'vintage'),
            power_level=template['power_level'],
            complexity=template['complexity'],
            themes=template.get('themes', []),
            is_singleton=is_singleton,
            is_peasant=is_peasant
        )
        
        target_size = template['size']
        color_dist = template['color_distribution']
        type_dist = template['type_distribution']
        rarity_dist = template['rarity_distribution']
        
        # Calculate target counts for each category
        color_targets = {color: int(count * target_size) for color, count in color_dist.items()}
        type_targets = {card_type: int(count * target_size) for card_type, count in type_dist.items()}
        rarity_targets = {rarity: int(count * target_size) for rarity, count in rarity_dist.items()}
        
        # Separate cards by type and rarity
        cards_by_type = {}
        cards_by_rarity = {}
        cards_by_color = {}
        
        for card in card_pool:
            # By type
            if card.type_line:
                primary_type = card.type_line.split(' —')[0].strip()
                if primary_type not in cards_by_type:
                    cards_by_type[primary_type] = []
                cards_by_type[primary_type].append(card)
            
            # By rarity
            if card.rarity:
                if card.rarity not in cards_by_rarity:
                    cards_by_rarity[card.rarity] = []
                cards_by_rarity[card.rarity].append(card)
            
            # By color
            card_colors = card.get_color_identity_list()
            if not card_colors:
                if 'C' not in cards_by_color:
                    cards_by_color['C'] = []
                cards_by_color['C'].append(card)
            else:
                for color in card_colors:
                    if color not in cards_by_color:
                        cards_by_color[color] = []
                    cards_by_color[color].append(card)
        
        # Add cards to cube
        added_cards = set()
        current_size = 0
        
        # Add cards by type and rarity
        for card_type, target_count in type_targets.items():
            if card_type in cards_by_type and target_count > 0:
                available_cards = [c for c in cards_by_type[card_type] if c.id not in added_cards]
                random.shuffle(available_cards)
                
                for card in available_cards[:target_count]:
                    if current_size >= target_size:
                        break
                    
                    # Check availability
                    if availability_ledger and availability_ledger.get(card.id, 0) <= 0:
                        continue
                    
                    # Check singleton rule
                    if is_singleton and card.id in added_cards:
                        continue
                    
                    cube.add_card(card)
                    added_cards.add(card.id)
                    current_size += 1
        
        # Fill remaining slots with random cards
        remaining_cards = [c for c in card_pool if c.id not in added_cards]
        random.shuffle(remaining_cards)
        
        for card in remaining_cards:
            if current_size >= target_size:
                break
            
            # Check availability
            if availability_ledger and availability_ledger.get(card.id, 0) <= 0:
                continue
            
            # Check singleton rule
            if is_singleton and card.id in added_cards:
                continue
            
            cube.add_card(card)
            added_cards.add(card.id)
            current_size += 1
        
        return cube
    
    def _evaluate_cube(self, cube: Cube, template: Dict) -> float:
        """Evaluate cube fitness score."""
        score = 0.0
        
        # Size scoring
        target_size = template['size']
        actual_size = cube.get_total_cards()
        size_penalty = abs(actual_size - target_size) / target_size
        score += max(0, 50 - size_penalty * 100)
        
        # Color distribution scoring
        color_dist = cube.get_color_distribution()
        target_colors = template['color_distribution']
        total_cards = sum(color_dist.values())
        
        if total_cards > 0:
            for color, target_ratio in target_colors.items():
                if color in color_dist:
                    actual_ratio = color_dist[color] / total_cards
                    color_penalty = abs(actual_ratio - target_ratio)
                    score += max(0, 20 - color_penalty * 200)
        
        # Type distribution scoring
        type_dist = cube.get_card_count_by_type()
        target_types = template['type_distribution']
        
        for card_type, target_ratio in target_types.items():
            if card_type in type_dist:
                actual_ratio = type_dist[card_type] / actual_size
                type_penalty = abs(actual_ratio - target_ratio)
                score += max(0, 15 - type_penalty * 150)
        
        # Mana curve scoring
        curve = cube.get_mana_curve()
        target_curve = template['mana_curve']
        
        for cmc, target_count in target_curve.items():
            actual_count = curve.get(cmc, 0)
            curve_penalty = abs(actual_count - target_count)
            score += max(0, 10 - curve_penalty * 0.1)
        
        # Theme scoring
        themes = template.get('themes', [])
        if themes:
            theme_score = self._evaluate_themes(cube, themes)
            score += theme_score
        
        # Power level scoring
        power_score = self._evaluate_power_level(cube, template['power_level'])
        score += power_score
        
        return score
    
    def _evaluate_themes(self, cube: Cube, themes: List[str]) -> float:
        """Evaluate how well the cube supports the given themes."""
        theme_score = 0.0
        
        for theme in themes:
            # Count cards that support this theme
            supporting_cards = 0
            for cc in cube.cards:
                if self._card_supports_theme(cc.card, theme):
                    supporting_cards += cc.quantity
            
            # Score based on theme support
            theme_ratio = supporting_cards / cube.get_total_cards()
            if theme_ratio > 0.1:  # At least 10% of cards support the theme
                theme_score += min(20, theme_ratio * 100)
        
        return theme_score
    
    def _card_supports_theme(self, card: Card, theme: str) -> bool:
        """Check if a card supports a specific theme."""
        text = (card.oracle_text or '').lower()
        type_line = (card.type_line or '').lower()
        
        theme_keywords = {
            'graveyard': ['graveyard', 'flashback', 'delve', 'disturb', 'unearth'],
            'artifacts': ['artifact', 'equipment', 'thopter', 'construct'],
            'tribal': ['elf', 'goblin', 'zombie', 'vampire', 'human', 'dragon'],
            'spells': ['instant', 'sorcery', 'prowess', 'whenever you cast'],
            'combo': ['sacrifice', 'when', 'enters', 'leaves', 'counter'],
            'control': ['counter', 'destroy', 'exile', 'return to hand'],
            'aggro': ['haste', 'trample', 'first strike', 'double strike'],
            'midrange': ['draw', 'gain', 'life', 'creature', 'permanent'],
            'ramp': ['add', 'mana', 'land', 'untap'],
            'storm': ['storm', 'copy', 'cast', 'spell']
        }
        
        if theme in theme_keywords:
            keywords = theme_keywords[theme]
            return any(keyword in text or keyword in type_line for keyword in keywords)
        
        return False
    
    def _evaluate_power_level(self, cube: Cube, target_power: str) -> float:
        """Evaluate the power level of the cube."""
        # This is a simplified power level evaluation
        # In practice, this would be more sophisticated
        
        power_scores = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9
        }
        
        target_score = power_scores.get(target_power, 0.6)
        
        # Calculate average power based on rarity distribution
        rarity_scores = {'common': 0.2, 'uncommon': 0.4, 'rare': 0.7, 'mythic': 0.9}
        total_power = 0
        total_cards = 0
        
        for cc in cube.cards:
            if cc.card.rarity in rarity_scores:
                total_power += rarity_scores[cc.card.rarity] * cc.quantity
                total_cards += cc.quantity
        
        if total_cards > 0:
            actual_power = total_power / total_cards
            power_penalty = abs(actual_power - target_score)
            return max(0, 20 - power_penalty * 50)
        
        return 0
    
    def _tournament_selection(self, fitness_scores: List[Tuple[Cube, float]], k: int) -> Cube:
        """Select cube using tournament selection."""
        tournament = random.sample(fitness_scores, min(k, len(fitness_scores)))
        return max(tournament, key=lambda x: x[1])[0]
    
    def _crossover(self, parent1: Cube, parent2: Cube, card_pool: List[Card], template: Dict, is_singleton: bool = True, is_peasant: bool = False) -> Cube:
        """Create child cube by crossing over two parents."""
        child = Cube(
            name=f"Generated {template['power_level'].title()} Cube",
            size=template['size'],
            format=template.get('format', 'vintage'),
            power_level=template['power_level'],
            complexity=template['complexity'],
            themes=template.get('themes', []),
            is_singleton=is_singleton,
            is_peasant=is_peasant
        )
        
        # Combine cards from both parents
        all_cards = parent1.cards + parent2.cards
        random.shuffle(all_cards)
        
        added_cards = set()
        current_size = 0
        target_size = template['size']
        
        for cc in all_cards:
            if cc.card.id not in added_cards and current_size < target_size:
                child.add_card(cc.card, cc.quantity, cc.is_basic_land, cc.cube_notes)
                added_cards.add(cc.card.id)
                current_size += cc.quantity
        
        # Fill remaining slots with random cards
        remaining_cards = [c for c in card_pool if c.id not in added_cards]
        random.shuffle(remaining_cards)
        
        for card in remaining_cards:
            if current_size >= target_size:
                break
            child.add_card(card)
            added_cards.add(card.id)
            current_size += 1
        
        return child
    
    def _mutate(self, cube: Cube, card_pool: List[Card], template: Dict, is_singleton: bool = True, is_peasant: bool = False) -> Cube:
        """Mutate cube by replacing random cards."""
        # Remove 5-10 random cards
        mutations = random.randint(5, 10)
        cards_to_remove = random.sample(cube.cards, min(mutations, len(cube.cards)))
        
        for cc in cards_to_remove:
            cube.remove_card(cc.card, cc.quantity)
        
        # Add random new cards
        available_cards = [c for c in card_pool if c.id not in {cc.card.id for cc in cube.cards}]
        random.shuffle(available_cards)
        
        for card in available_cards[:mutations]:
            if cube.get_total_cards() >= template['size']:
                break
            cube.add_card(card)
        
        return cube
