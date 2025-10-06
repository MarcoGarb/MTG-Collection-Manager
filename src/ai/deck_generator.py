"""
AI-powered deck generator using genetic algorithm and unified analyzer.
"""
import random
from typing import List, Optional, Dict, Tuple
from src.models.card import Card
from src.models.deck import Deck, DeckCard
from src.ai.deck_analyzer import DeckAnalyzer
from datetime import datetime


class DeckGenerator:
    """Generate optimized decks using genetic algorithm."""
    
    # Archetype templates
    ARCHETYPE_TEMPLATES = {
        'aggro': {
            'curve': {1: 12, 2: 14, 3: 10, 4: 4, 5: 2, 6: 0},
            'lands': 20,
            'creatures': 0.60,  # 60% creatures
            'removal': 0.15,
            'other': 0.05,
        },
        'midrange': {
            'curve': {1: 4, 2: 10, 3: 12, 4: 10, 5: 6, 6: 2},
            'lands': 24,
            'creatures': 0.45,
            'removal': 0.20,
            'other': 0.15,
        },
        'control': {
            'curve': {1: 2, 2: 8, 3: 8, 4: 10, 5: 8, 6: 4},
            'lands': 26,
            'creatures': 0.15,
            'removal': 0.30,
            'other': 0.25,
        },
        'combo': {
            'curve': {1: 8, 2: 12, 3: 8, 4: 6, 5: 4, 6: 2},
            'lands': 24,
            'creatures': 0.25,
            'removal': 0.10,
            'other': 0.45,
        }
    }
    
    def __init__(self, collection: List[Card]):
        self.collection = collection
        self.analyzer = DeckAnalyzer()
    
    
    def _filter_by_colors(self, colors: List[str]) -> List[Card]:
        """
        Filter collection to only include cards matching the color identity.
    
        Args:
            colors: List of color codes (e.g., ['R', 'G'])
        
        Returns:
            List of cards that match the color identity
        """
        if not colors:
            return self.collection
    
        color_set = set(colors)
        filtered = []
    
        for card in self.collection:
            # Get card's color identity
            card_colors = set(card.get_color_identity_list())
        
            # Include colorless cards (they can go in any deck)
            if not card_colors:
                filtered.append(card)
                continue
        
            # Include cards whose colors are a subset of deck colors
            if card_colors.issubset(color_set):
                filtered.append(card)
    
        return filtered

    def generate_deck(
        self,
        archetype: str = 'midrange',
        format: str = 'standard',
        colors: List[str] = None,
        deck_size: int = 60,
        commander: Optional[Card] = None,
        auto_select_commander: bool = True
    ) -> Deck:
        """Generate a deck using genetic algorithm."""
    
        print(f"🔍 Starting deck generation: {archetype} in {format}")
    
        # Validate archetype
        if archetype not in self.ARCHETYPE_TEMPLATES:
            raise ValueError(f"Unknown archetype: {archetype}")
    
        # Default colors
        if colors is None:
            colors = ['R']
    
        print(f"🔍 Colors: {colors}")
    
        # Handle Commander format
        if format.lower() == 'commander':
            deck_size = 99  # Commander is the 100th card
            print(f"🔍 Commander format detected, deck_size={deck_size}")
        
            # Auto-select commander if not provided
            if commander is None and auto_select_commander:
                valid_cards = self._filter_by_colors(colors)
                suitable_commanders = self._find_suitable_commanders(valid_cards, colors)
            
                if suitable_commanders:
                    commander = random.choice(suitable_commanders)
                    print(f"🎯 Auto-selected commander: {commander.name}")
                else:
                    print("⚠️ No suitable commander found")
    
        # Filter collection by colors
        valid_cards = self._filter_by_colors(colors)
        print(f"🔍 Filtered to {len(valid_cards)} valid cards")
    
        if not valid_cards:
            raise ValueError(f"No cards found for colors: {colors}")
    
        # Run genetic algorithm
        print(f"🧬 Running genetic algorithm...")
        best_deck = self._genetic_algorithm(
            valid_cards,
            archetype,
            deck_size,
            format,
            commander
        )
    
        # Safety check
        if best_deck is None:
            raise ValueError("Genetic algorithm returned None!")
    
        print(f"✅ Generated deck: {best_deck.name}")
    
        # Enforce singleton for commander format
        if format.lower() == 'commander':
            print(f"🔍 Enforcing singleton rule...")
            best_deck = self._enforce_singleton(best_deck)
    
        # Update deck metadata
        best_deck.update_colors()
        best_deck.date_modified = datetime.now().isoformat()
    
        print(f"✅ Deck generation complete!")
        return best_deck

    def _find_suitable_commanders(self, card_pool: List[Card], colors: List[str]) -> List[Card]:
        """Find suitable commanders from the card pool."""
        suitable = []
        color_set = set(colors)
    
        for card in card_pool:
            # Must be legendary creature
            if not card.type_line:
                continue
        
            if 'Legendary' in card.type_line and 'Creature' in card.type_line:
                # Check color identity matches
                card_colors = set(card.get_color_identity_list())
            
                # Commander's color identity must be subset of deck colors
                # OR deck colors must be subset of commander's colors
                if card_colors.issubset(color_set) or color_set.issubset(card_colors):
                    suitable.append(card)
    
        return suitable

    def _enforce_singleton(self, deck: Deck) -> Deck:
        """Convert deck to singleton format (max 1 of each card except basic lands)."""
    
        # Get commander BEFORE doing anything
        commander_dc = deck.get_commander()
    
        if not commander_dc:
            print("⚠️ WARNING: No commander found in deck during singleton enforcement!")
        else:
            print(f"🔍 Found commander: {commander_dc.card.name}")
    
        # Get all mainboard cards
        all_cards = deck.get_mainboard_cards()
    
        # Separate cards by type
        singleton_cards = []
        basic_lands = []
        seen_ids = set()
    
        for dc in all_cards:
            # Skip commander - we'll add it back separately
            if dc.is_commander:
                continue
        
            is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line
        
            if is_basic:
                # Keep basic lands (can have multiple copies)
                basic_lands.append(dc)
            elif dc.card.id not in seen_ids:
                # Enforce singleton for non-basic cards
                singleton_cards.append(DeckCard(
                    card=dc.card,
                    quantity=1,
                    is_commander=False,
                    in_sideboard=False
                ))
                seen_ids.add(dc.card.id)
    
        # Calculate current size (excluding commander)
        current_size = len(singleton_cards) + sum(dc.quantity for dc in basic_lands)
        target_size = 99  # Commander deck needs 99 + 1 commander = 100
    
        print(f"🔍 Before adjustment: {current_size} cards (target: {target_size})")
    
        # Adjust to hit exactly 99 cards
        if current_size < target_size:
            shortage = target_size - current_size
            print(f"⚠️ Shortage: {shortage} cards")
            if basic_lands:
                basic_lands[0].quantity += shortage
            else:
                print("⚠️ No basic lands to adjust!")
        elif current_size > target_size:
            excess = current_size - target_size
            print(f"⚠️ Excess: {excess} cards")
            for bl in basic_lands:
                if excess <= 0:
                    break
                reduction = min(excess, bl.quantity - 1)
                bl.quantity -= reduction
                excess -= reduction
    
        # Clear and rebuild deck
        deck.cards.clear()
    
        # Add commander FIRST
        if commander_dc:
            deck.cards.append(DeckCard(
                card=commander_dc.card,
                quantity=1,
                is_commander=True,
                in_sideboard=False
            ))
            print(f"✅ Re-added commander: {commander_dc.card.name}")
    
        # Add all other cards
        deck.cards.extend(singleton_cards)
        deck.cards.extend(basic_lands)
    
        # Verify
        final_commander = deck.get_commander()
        if final_commander:
            print(f"✅ Commander verified in final deck: {final_commander.card.name}")
        else:
            print(f"❌ Commander MISSING in final deck!")
    
        return deck
    
    def _genetic_algorithm(
        self,
        card_pool: List[Card],
        archetype: str,
        deck_size: int,
        format: str,
        commander: Optional[Card]
    ) -> Deck:
    
        print(f"🔍 DEBUG: GA Parameters:")
        print(f"   Card pool size: {len(card_pool)}")
        print(f"   Target deck size: {deck_size}")
        print(f"   Format: {format}")
        print(f"   Commander: {commander.name if commander else 'None'}")
        
        # GA parameters
        POPULATION_SIZE = 50
        GENERATIONS = 100
        MUTATION_RATE = 0.15
        ELITE_SIZE = 5
        
        # Initialize population
        population = [self._create_random_deck(card_pool, archetype, deck_size, format, commander)
                     for _ in range(POPULATION_SIZE)]

        best_score = -float('inf')  # Start with negative infinity
        best_deck = population[0] if population else None  # Initialize with first deck
        generations_without_improvement = 0

        # Safety check
        if not population or best_deck is None:
            raise ValueError("Failed to create initial population")
        
        for generation in range(GENERATIONS):
            # Evaluate fitness
            fitness_scores = [(deck, self._evaluate_deck(deck, archetype)) for deck in population]
            fitness_scores.sort(key=lambda x: -x[1])
            
            current_best_score = fitness_scores[0][1]
            
            if current_best_score > best_score:
                best_score = current_best_score
                best_deck = fitness_scores[0][0]
                generations_without_improvement = 0
                print(f"Generation {generation}: Best score = {best_score:.2f}")
            else:
                generations_without_improvement += 1
            
            # Early stopping if no improvement
            if generations_without_improvement > 20:
                print(f"Converged at generation {generation}")
                break
            
            # Selection: Keep elite
            new_population = [deck for deck, score in fitness_scores[:ELITE_SIZE]]
            
            # Crossover and mutation
            while len(new_population) < POPULATION_SIZE:
                # Tournament selection
                parent1 = self._tournament_selection(fitness_scores, 5)
                parent2 = self._tournament_selection(fitness_scores, 5)
                
                # Crossover
                child = self._crossover(parent1, parent2, card_pool, deck_size)
                
                # Mutation
                if random.random() < MUTATION_RATE:
                    child = self._mutate(child, card_pool, archetype, deck_size)
                
                new_population.append(child)
            
            population = new_population
        
        print(f"Final best score: {best_score:.2f}")
    
        # Safety check: ensure we return a valid deck
        if best_deck is None:
            print("⚠️ WARNING: best_deck is None, using first from population")
            if population:
                best_deck = population[0]
            else:
                raise ValueError("No valid deck generated!")

        return best_deck
    
    def _create_random_deck(
        self,
        card_pool: List[Card],
        archetype: str,
        deck_size: int,
        format: str,
        commander: Optional[Card]
    ) -> Deck:
        """Create a random deck from card pool following archetype guidelines."""
    
        deck = Deck(
            name=f"{archetype.title()} Deck",
            format=format,
            description=f"AI-generated {archetype} deck"
        )
    
        # Add commander first if provided
        if commander:
            deck.add_card(commander, quantity=1, is_commander=True)
    
        # Get archetype template
        template = self.ARCHETYPE_TEMPLATES[archetype]
    
        # Separate lands from nonlands
        lands = [c for c in card_pool if c.is_land()]
        nonlands = [c for c in card_pool if not c.is_land()]
    
        # Calculate target counts
        target_lands = int(deck_size * template['lands'])
        target_nonlands = deck_size - target_lands
    
        # For commander format (singleton), each card is quantity 1
        is_singleton = format.lower() == 'commander'
    
        # Add nonland cards
        random.shuffle(nonlands)
        added_nonlands = 0
        for card in nonlands:
            if added_nonlands >= target_nonlands:
                break
            qty = 1 if is_singleton else random.randint(1, 4)
            qty = min(qty, target_nonlands - added_nonlands)
            deck.add_card(card, quantity=qty)
            added_nonlands += qty
    
        # Add land cards
        random.shuffle(lands)
        added_lands = 0
        for card in lands:
            if added_lands >= target_lands:
                break
        
            # Basic lands can be multiple copies even in Commander
            is_basic = card.type_line and 'Basic Land' in card.type_line
        
            if is_singleton and not is_basic:
                qty = 1
            else:
                qty = random.randint(3, 8) if is_basic else random.randint(1, 4)
        
            qty = min(qty, target_lands - added_lands)
            deck.add_card(card, quantity=qty)
            added_lands += qty
    
        # Fill remaining slots if needed
        current_size = sum(dc.quantity for dc in deck.get_mainboard_cards() if not dc.is_commander)
    
        if current_size < deck_size:
            print(f"⚠️ Deck undersized ({current_size}/{deck_size}), filling...")
            added_ids = {dc.card.id for dc in deck.cards}
        
            for card in card_pool:
                if current_size >= deck_size:
                    break
                if card.id not in added_ids:
                    qty = 1 if is_singleton else min(2, deck_size - current_size)
                    deck.add_card(card, quantity=qty)
                    added_ids.add(card.id)
                    current_size += qty
    
        return deck
    
    def _evaluate_deck(self, deck: Deck, archetype: str) -> float:
        """Evaluate deck fitness score."""
        try:
            self.analyzer = DeckAnalyzer(deck)
            analysis = self.analyzer.analyze_deck()
        except:
            return 0.0
        
        score = 0.0
        template = self.ARCHETYPE_TEMPLATES[archetype]
        
        # Mana curve scoring
        curve = analysis['mana_curve']
        ideal_curve = template['curve']
        
        curve_score = 0
        for cmc, ideal_count in ideal_curve.items():
            actual_count = curve.get(cmc, 0)
            deviation = abs(actual_count - ideal_count)
            curve_score += max(0, 10 - deviation)
        
        score += curve_score * 2  # Weight: 2x
        
        # Card type distribution
        card_types = analysis['card_types']
        mainboard = deck.get_mainboard_cards()
        total_nonlands = sum(dc.quantity for dc in mainboard if not dc.card.is_land())
        
        if total_nonlands > 0:
            creature_ratio = card_types.get('creature', 0) / total_nonlands
            ideal_creature_ratio = template['creatures']
            creature_score = max(0, 20 - abs(creature_ratio - ideal_creature_ratio) * 100)
            score += creature_score
        
        # Synergy scoring
        themes = analysis['themes']
        if themes:
            # Reward having focused themes
            max_theme_count = max(themes.values())
            synergy_score = min(30, max_theme_count * 2)
            score += synergy_score
        
        # Interaction scoring based on archetype
        removal_count = analysis['removal_count']
        if archetype == 'control':
            score += min(30, removal_count * 2)
        elif archetype == 'aggro':
            score += min(15, removal_count)
        else:
            score += min(20, removal_count * 1.5)
        
        # Card draw
        draw_count = analysis['card_draw_count']
        score += min(15, draw_count * 2)
        
        # Color balance (penalize if too many colors)
        color_count = len(analysis['colors'])
        if color_count <= 2:
            score += 10
        elif color_count == 3:
            score += 5
        
        return score
    
    def _tournament_selection(self, fitness_scores: List[Tuple[Deck, float]], k: int) -> Deck:
        """Select deck using tournament selection."""
        tournament = random.sample(fitness_scores, min(k, len(fitness_scores)))
        return max(tournament, key=lambda x: x[1])[0]
    
    def _crossover(self, parent1: Deck, parent2: Deck, card_pool: List[Card], deck_size: int) -> Deck:
        """Create child deck by crossing over two parents."""
        child = Deck(
            name="Generated Deck",
            format=parent1.format,
            description="AI-generated deck"
        )
    
        # Preserve commander from parent1 if it exists
        p1_commander = parent1.get_commander()
        if p1_commander:
            child.add_card(p1_commander.card, quantity=1, is_commander=True)
            deck_size = deck_size - 1  # Adjust for commander
    
        # Get non-commander cards from both parents
        p1_cards = [dc for dc in parent1.get_mainboard_cards() if not dc.is_commander]
        p2_cards = [dc for dc in parent2.get_mainboard_cards() if not dc.is_commander]
    
        # Mix cards from both parents
        all_cards = p1_cards + p2_cards
        random.shuffle(all_cards)
    
        added_cards = set()
        current_size = 0
    
        for dc in all_cards:
            if dc.card.id not in added_cards and current_size < deck_size:
                qty = min(dc.quantity, deck_size - current_size)
                child.add_card(dc.card, quantity=qty)
                added_cards.add(dc.card.id)
                current_size += qty
    
        # Fill to deck size if needed
        while current_size < deck_size:
            random_card = random.choice(card_pool)
            if random_card.id not in added_cards:
                qty = min(2, deck_size - current_size)
                child.add_card(random_card, quantity=qty)
                added_cards.add(random_card.id)
                current_size += qty
    
        return child
    
    def _mutate(self, deck: Deck, card_pool: List[Card], archetype: str, deck_size: int) -> Deck:
        """Mutate deck by replacing random cards."""
        # Get non-commander mainboard cards
        mainboard = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
    
        if not mainboard:
            return deck
    
        # Replace 1-3 random cards
        mutations = random.randint(1, 3)
    
        for _ in range(mutations):
            if mainboard:
                # Remove random non-commander card
                remove_dc = random.choice(mainboard)
                deck.remove_card(remove_dc.card)
                mainboard.remove(remove_dc)
            
                # Add random new card
                new_card = random.choice(card_pool)
                qty = min(random.randint(1, 3), remove_dc.quantity)
                deck.add_card(new_card, quantity=qty)
    
        return deck