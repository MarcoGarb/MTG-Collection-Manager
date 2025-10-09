"""
AI-powered deck generator using genetic algorithm and unified analyzer.
"""
import random
from typing import List, Optional, Dict, Tuple
from src.models.card import Card
from src.models.deck import Deck, DeckCard
from src.ai.deck_analyzer import DeckAnalyzer
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

# Basic lands mapping for virtual/unlimited creation
BASIC_LANDS = {
    'Plains':  {'color': 'W', 'type': 'Basic Land — Plains',  'text': '({T}: Add {W}.)'},
    'Island':  {'color': 'U', 'type': 'Basic Land — Island',  'text': '({T}: Add {U}.)'},
    'Swamp':   {'color': 'B', 'type': 'Basic Land — Swamp',   'text': '({T}: Add {B}.)'},
    'Mountain':{'color': 'R', 'type': 'Basic Land — Mountain','text': '({T}: Add {R}.)'},
    'Forest':  {'color': 'G', 'type': 'Basic Land — Forest',  'text': '({T}: Add {G}.)'},
    'Wastes':  {'color': 'C', 'type': 'Basic Land — Wastes',  'text': '({T}: Add {C}.)'},
}
def _basic_for_color(c: str) -> str:
    m = {'W': 'Plains', 'U': 'Island', 'B': 'Swamp', 'R': 'Mountain', 'G': 'Forest', 'C': 'Wastes'}
    return m.get(c.upper(), 'Wastes')
def _make_basic_land(name: str) -> Card:
    info = BASIC_LANDS[name]
    # Virtual Card; negative id helps distinguish from DB ids
    return Card(
        id=-ord(name[0]),
        name=name,
        set_code='BASIC',
        collector_number='0',
        rarity='common',
        mana_cost='',
        cmc=0.0,
        colors=info['color'],
        color_identity=info['color'],
        type_line=info['type'],
        card_types='Land,Basic',
        subtypes=name,
        oracle_text=info['text'],
        quantity=999
    )
def _count_color_pips(deck: Deck) -> dict:
    """Count colored mana symbols in nonland mana costs to guide basic-land mix."""
    counts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}
    for dc in deck.get_mainboard_cards():
        if dc.card.is_land():
            continue
        cost = dc.card.mana_cost or ''
        q = dc.quantity
        for c in counts.keys():
            counts[c] += cost.count(f'{{{c}}}') * q
            # Include hybrid symbols both sides
            counts[c] += cost.count(f'{c}/') * q
            counts[c] += cost.count(f'/{c}') * q
    return counts
def _target_land_count(fmt: str, archetype: str, deck_size: int) -> int:
    """Reasonable targets. We don't trust the template's 'lands' raw value."""
    fmt = (fmt or '').lower()
    if fmt == 'commander':
        return 37  # common default (can vary 35–40)
    baseline = {
        'aggro': 20,
        'midrange': 24,
        'control': 26,
        'combo': 24,
        'tribal': 24,
    }.get(archetype, 24)
    # Scale for non-60 sizes just in case
    return max(16, round(baseline * (deck_size / 60.0)))
def _color_mix_from_pips(pips: dict, colors: list) -> dict:
    """Return proportions per color from pip counts; fallback to even split."""
    active = [c for c in (colors or []) if c in 'WUBRG']
    if not active:
        return {}
    total = sum(pips.get(c, 0) for c in active)
    if total == 0:
        # Even split if no pips found
        return {c: 1.0 / len(active) for c in active}
    return {c: (pips.get(c, 0) / total) for c in active}

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
        },
        'tribal': {
        'curve': {1: 6, 2: 10, 3: 12, 4: 8, 5: 4, 6: 2},
        'lands': 24,
        'creatures': 0.55,
        'removal': 0.15,
        'other': 0.15,
    },
    }
    
    def __init__(self, collection: List[Card]):
        self.collection = collection
        self.analyzer = DeckAnalyzer()
        self._target_tribe: Optional[str] = None  # NEW
    
    
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
        auto_select_commander: bool = True,
        tribe: Optional[str] = None,
        availability_ledger: Optional[Dict[int, int]] = None,
        current_deck_id: Optional[int] = None
    ) -> Deck:
        """Generate a deck using a genetic algorithm."""
        print(f"🔍 Starting deck generation: {archetype} in {format}")

        # Validate archetype
        if archetype not in self.ARCHETYPE_TEMPLATES:
            raise ValueError(f"Unknown archetype: {archetype}")

        # Default colors
        if colors is None:
            colors = ['R']
        print(f"🔍 Colors: {colors}")

        # Tribal target
        self._target_tribe = None
        if archetype == 'tribal' and isinstance(tribe, str) and tribe.strip():
            self._target_tribe = tribe.strip().lower()

        # 1) Filter the collection by colors first so valid_cards exists
        valid_cards = self._filter_by_colors(colors)

        # If tribal, reorder/favor tribe hits in the pool
        if self._target_tribe:
            def is_tribal(c: Card) -> bool:
                tl = (c.type_line or '').lower()
                tx = (c.oracle_text or '').lower()
                t = self._target_tribe
                return (t in tl) or (t in tx)
            tribal_first = [c for c in valid_cards if is_tribal(c)]
            others = [c for c in valid_cards if c not in tribal_first]
            valid_cards = tribal_first + others

        print(f"🔍 Filtered to {len(valid_cards)} valid cards")
        if not valid_cards:
            raise ValueError(f"No cards found for colors: {colors}")

        # 2) Optional availability filter (keep basics unlimited)
        if availability_ledger:
            before = len(valid_cards)
            valid_cards = [
                c for c in valid_cards
                if ('Basic Land' in (c.type_line or ''))
                or availability_ledger.get(getattr(c, 'id', None), 0) > 0
            ]
            print(f"🔍 Availability filter: {before} -> {len(valid_cards)}")

        # 3) Commander handling AFTER valid_cards is set (fixes NameError)
        if format.lower() == 'commander':
            deck_size = 99
            if commander is None and auto_select_commander:
                suitable_commanders = self._find_suitable_commanders(valid_cards, colors)
                # Respect availability for commander choice
                if availability_ledger:
                    suitable_commanders = [
                        c for c in suitable_commanders
                        if availability_ledger.get(getattr(c, 'id', None), 0) > 0
                    ]
                if suitable_commanders:
                    commander = random.choice(suitable_commanders)
                    print(f"🎯 Auto-selected commander: {commander.name}")
                else:
                    print("⚠️ No suitable commander found with availability")

        # 4) Run GA on the properly prepared pool
        print("🧬 Running genetic algorithm...")
        best_deck = self._genetic_algorithm(
            valid_cards,
            archetype,
            deck_size,
            format,
            commander
        )
        if best_deck is None:
            raise ValueError("Genetic algorithm returned None!")

        print(f"✅ Generated deck: {best_deck.name}")

        # 5) Commander-specific enforcement
        if format.lower() == 'commander':
            print("🔍 Enforcing singleton rule...")
            best_deck = self._enforce_singleton(best_deck)
            # FINAL land clamp and keep body at 99
            best_deck = self._cap_commander_lands(best_deck, valid_cards, min_lands=35, max_lands=40)

        # 6) Enforce availability ledger for ALL formats (not just commander)
        if availability_ledger:
            best_deck = self._enforce_availability(
                best_deck, availability_ledger, format=format, colors=colors
            )

        # 7) Ensure a sensible land base EVEN IF collection lacked basics (this was unreachable before)
        try:
            self._ensure_land_base(best_deck, colors or [], format, archetype, deck_size)
        except Exception:
            # Never let land-base adjustment break generation
            pass

        # 8) Ensure deck meets format minimum card counts (fill with nonlands then basics)
        try:
            fmt_l = (format or '').lower()
            # Prefer format rules min_cards if available, else use deck_size
            min_req = Deck.FORMAT_RULES.get(fmt_l, {}).get('min_cards', deck_size)
            # For commander, min_cards is typically 100 (including commander)
            self._ensure_min_deck_size(best_deck, fmt_l, min_req, valid_cards)
        except Exception:
            # Don't let this break generation
            pass

        # 9) Enforce copy limits (e.g., max 4 copies) to avoid invalid decks like >4 copies
        try:
            max_copies = Deck.FORMAT_RULES.get((format or '').lower(), {}).get('max_copies', None)
            if max_copies and max_copies > 0:
                self._enforce_copy_limits(best_deck, max_copies, valid_cards, format=(format or '').lower())
        except Exception:
            pass

        # If Commander format, ensure there are no duplicate copies of the commander card
        try:
            if (format or '').lower() == 'commander':
                self._ensure_single_commander_copy(best_deck)
        except Exception:
            pass

        # FINAL: ensure deck still meets format minimums after all post-processing (copy clamping etc.)
        try:
            fmt_l = (format or '').lower()
            min_req = Deck.FORMAT_RULES.get(fmt_l, {}).get('min_cards', deck_size)
            # valid_cards should be available from earlier; fall back to full collection
            pool = valid_cards if 'valid_cards' in locals() else self.collection
            self._ensure_min_deck_size(best_deck, fmt_l, min_req, pool)
        except Exception:
            pass

        best_deck.update_colors()
        best_deck.date_modified = datetime.now().isoformat()
        return best_deck

    def _ensure_single_commander_copy(self, deck: Deck) -> Deck:
        """Remove any non-commander copies of the commander so only the commander entry remains."""
        try:
            commander_dc = deck.get_commander()
            if not commander_dc:
                return deck
            commander_id = commander_dc.card.id

            # Remove any non-commander deck entries with same id
            new_cards = []
            for dc in deck.cards:
                if dc.is_commander:
                    new_cards.append(dc)
                else:
                    if getattr(dc.card, 'id', None) == commander_id:
                        # skip duplicate non-commander copy
                        continue
                    new_cards.append(dc)

            deck.cards = new_cards
        except Exception as exc:
            print(f"⚠️ _ensure_single_commander_copy failed: {exc}")
        # If removal caused deck to drop below commander minimum, top up with basics
        try:
            min_cards = Deck.FORMAT_RULES.get('commander', {}).get('min_cards', 100)
            current_mb = deck.mainboard_count()
            if current_mb < min_cards:
                to_add = min_cards - current_mb
                colors = deck.get_colors() or []
                self._add_basic_lands(deck, to_add, colors)
        except Exception:
            pass
        return deck

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
        seen_names = set()

        for dc in all_cards:
            # Skip commander - we'll add it back separately
            if dc.is_commander:
                continue
            # Also skip any card that is the commander (same id) to avoid duplicate copies
            if commander_dc and dc.card.id == commander_dc.card.id:
                continue

            is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line

            if is_basic:
                # Keep basic lands (can have multiple copies)
                basic_lands.append(dc)
            else:
                # Use card name (normalized) to enforce singleton across printings
                name = (dc.card.name or '').strip().lower()
                if name and name not in seen_names:
                    singleton_cards.append(DeckCard(
                        card=dc.card,
                        quantity=1,
                        is_commander=False,
                        in_sideboard=False
                    ))
                    seen_names.add(name)
    
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
    
    def _cap_commander_lands(self, deck: Deck, card_pool: List[Card], min_lands: int = 35, max_lands: int = 40) -> Deck:
        """Clamp Commander land count into [min_lands, max_lands] and keep mainboard at 99 (excl. commander)."""
        is_commander = deck.format.lower() == 'commander'
        if not is_commander:
            return deck

        main = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
        body_size = 99
        land_dcs = [dc for dc in main if dc.card.is_land()]
        nonland_dcs = [dc for dc in main if not dc.card.is_land()]

        land_count = sum(dc.quantity for dc in land_dcs)
        nonland_count = sum(dc.quantity for dc in nonland_dcs)

        # Step 1: If too many lands, trim basics first then nonbasics
        if land_count > max_lands:
            excess = land_count - max_lands

            # Trim basics first (highest quantities first)
            basics = [dc for dc in land_dcs if 'Basic Land' in (dc.card.type_line or '')]
            basics.sort(key=lambda dc: dc.quantity, reverse=True)
            for dc in basics:
                if excess <= 0:
                    break
                reducible = min(excess, dc.quantity - 1)  # keep at least 1 copy of that basic
                if reducible > 0:
                    deck.remove_card(dc.card, quantity=reducible)
                    excess -= reducible
                    land_count -= reducible

            # If still too many lands, remove some nonbasics (singleton)
            if excess > 0:
                for dc in [d for d in land_dcs if 'Basic Land' not in (d.card.type_line or '')]:
                    if excess <= 0:
                        break
                    deck.remove_card(dc.card, quantity=1)
                    excess -= 1
                    land_count -= 1

        # Step 2: If too few lands and we have room, add basics to min_lands
        main = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
        current_body = sum(dc.quantity for dc in main)
        if land_count < min_lands and current_body < body_size:
            to_add = min(min_lands - land_count, body_size - current_body)
            colors = deck.get_colors() or []
            if not colors:
                colors = ['C']  # colorless fallback

            # Even distribution among deck colors
            per = max(1, to_add // max(1, len(colors)))
            remaining = to_add
            for i, c in enumerate(colors):
                if remaining <= 0:
                    break
                add = per if i < len(colors) - 1 else remaining
                name = {'W': 'Plains', 'U': 'Island', 'B': 'Swamp', 'R': 'Mountain', 'G': 'Forest'}.get(c, 'Wastes')
                basic = Card(
                    id=-ord(name[0]), name=name, set_code='BASIC', collector_number='0',
                    rarity='common', mana_cost='', cmc=0.0, colors=c if c != 'C' else '',
                    color_identity=c if c != 'C' else '', type_line=f'Basic Land — {name}',
                    card_types='Land,Basic', subtypes=name, oracle_text=f'({{T}}: Add {{{c}}}.)' if c != 'C' else '({T}: Add {C}.)',
                    quantity=999
                )
                deck.add_card(basic, quantity=add)
                remaining -= add
            land_dcs = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander and dc.card.is_land()]
            land_count = sum(dc.quantity for dc in land_dcs)

        # Step 3: After trims, backfill to 99 with nonlands
        main = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
        current_body = sum(dc.quantity for dc in main)
        if current_body < body_size:
            need = body_size - current_body
            added_ids = {dc.card.id for dc in main}
            # prefer nonlands not already in deck
            for card in card_pool:
                if need <= 0:
                    break
                if card.is_land():
                    continue
                if card.id in added_ids:
                    continue
                deck.add_card(card, quantity=1)
                added_ids.add(card.id)
                need -= 1

            # If pool exhausted, no-op; we stay <= 99 gracefully.

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
        """Create a random deck from card pool following archetype guidelines (fixed land math)."""
        import random

        deck = Deck(
            name=f"{archetype.title()} Deck",
            format=format,
            description=f"AI-generated {archetype} deck"
        )

        # Commander occupies a separate slot; deck_size here is non-commander body size
        is_commander = format.lower() == 'commander'
        if commander:
            deck.add_card(commander, quantity=1, is_commander=True)

        template = self.ARCHETYPE_TEMPLATES[archetype]

        # Target land counts (absolute, not ratio)
        if is_commander:
            target_lands = 37  # common default; we also cap later
            target_lands = min(target_lands, deck_size)  # safety
        else:
            target_lands = min(int(template['lands']), deck_size)

        target_nonlands = max(0, deck_size - target_lands)

        # Split pool
        lands = [c for c in card_pool if c.is_land()]
        nonlands = [c for c in card_pool if not c.is_land()]

        # Add nonlands first
        random.shuffle(nonlands)
        added_nonlands = 0
        commander_id = commander.id if commander else None
        for card in nonlands:
            if added_nonlands >= target_nonlands:
                break
            qty = 1 if is_commander else random.randint(1, 4)
            qty = min(qty, target_nonlands - added_nonlands)
            if qty <= 0:
                continue
            # If this is a commander deck, avoid adding the commander card as a non-commander copy
            if is_commander and commander_id is not None and card.id == commander_id:
                continue
            deck.add_card(card, quantity=qty)
            added_nonlands += qty

        # Add lands (singleton for nonbasic in Commander; basics can be >1)
        random.shuffle(lands)
        added_lands = 0
        for card in lands:
            if added_lands >= target_lands:
                break
            is_basic = ('Basic Land' in (card.type_line or ''))

            qty = 1 if (is_commander and not is_basic) else (random.randint(3, 8) if is_basic else random.randint(1, 4))
            qty = min(qty, target_lands - added_lands)
            if qty <= 0:
                continue

            if is_commander and not is_basic:
                # enforce singleton
                if any(dc.card.id == card.id for dc in deck.get_mainboard_cards() if not dc.is_commander):
                    continue
                qty = 1

            deck.add_card(card, quantity=qty)
            added_lands += qty

        # Fill remaining to body size (prefer nonlands to avoid land bloat)
        current_size = sum(dc.quantity for dc in deck.get_mainboard_cards() if not dc.is_commander)
        remaining = deck_size - current_size

        if remaining > 0:
            # Prefer nonlands
            for card in nonlands:
                if remaining <= 0:
                    break
                if is_commander and commander_id is not None and card.id == commander_id:
                    continue
                qty = 1 if is_commander else min(2, remaining)
                deck.add_card(card, quantity=qty)
                remaining -= qty

            # Absolute last resort: use lands to fill (clamped by remaining)
            if remaining > 0:
                for card in lands:
                    if remaining <= 0:
                        break
                    is_basic = ('Basic Land' in (card.type_line or ''))
                    if is_commander and commander_id is not None and not is_basic and card.id == commander_id:
                        continue
                    qty = 1 if (is_commander and not is_basic) else min(2, remaining)
                    deck.add_card(card, quantity=qty)
                    remaining -= qty

        # Ensure we never exceed body size
        main = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
        total_mb = sum(dc.quantity for dc in main)
        if total_mb > deck_size:
            excess = total_mb - deck_size
            # Trim lands first (prefer trimming basics)
            for dc in sorted((d for d in main if d.card.is_land()),
                            key=lambda d: 0 if 'Basic Land' in (d.card.type_line or '') else 1):
                if excess <= 0:
                    break
                reducible = min(excess, dc.quantity - (1 if is_commander and 'Basic Land' in (dc.card.type_line or '') else 0))
                if reducible > 0:
                    deck.remove_card(dc.card, quantity=reducible)
                    excess -= reducible

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

        # Tribal synergy bonus if requested
        if getattr(self, '_target_tribe', None):
            tribe = self._target_tribe
            tribal_count = 0
            for dc in deck.get_mainboard_cards():
                tl = (dc.card.type_line or '').lower()
                tx = (dc.card.oracle_text or '').lower()
                if tribe in tl or tribe in tx:
                    tribal_count += dc.quantity
            # Reward focused tribal presence, capped
            score += min(30, tribal_count * 1.5)
        
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
    
    def _ensure_land_base(self, deck: Deck, colors: List[str], fmt: str, archetype: str, deck_size: int):
        """Add/adjust basic lands to hit target land count, even if none in collection."""
        target = _target_land_count(fmt, archetype, deck_size)
        mainboard = deck.get_mainboard_cards()
        land_count = sum(dc.quantity for dc in mainboard if dc.card.is_land())
        need = max(0, target - land_count)
        if need == 0 and sum(dc.quantity for dc in mainboard if not dc.is_commander) == deck_size:
            return
        # If we need to add lands but deck is already full, free slots from the end (nonlands)
        current_size = sum(dc.quantity for dc in mainboard if not dc.is_commander)
        if current_size + need > deck_size:
            to_remove = min(need, (current_size + need) - deck_size)
            # Remove from nonlands one by one
            for dc in list(reversed(mainboard)):
                if to_remove <= 0: break
                if dc.card.is_land() or dc.is_commander: continue
                remove_now = min(dc.quantity, to_remove)
                deck.remove_card(dc.card, quantity=remove_now, from_sideboard=False)
                to_remove -= remove_now
        # Recompute remaining slots and need
        mainboard = deck.get_mainboard_cards()
        land_count = sum(dc.quantity for dc in mainboard if dc.card.is_land())
        current_size = sum(dc.quantity for dc in mainboard if not dc.is_commander)
        need = min(target - land_count, max(0, deck_size - current_size))
        if need <= 0:
            return
        # Compute colored pip mix → basic mix
        pips = _count_color_pips(deck)
        mix = _color_mix_from_pips(pips, colors)
        if not mix:
            # Fallback: even split by deck colors, else default to one colorless
            if colors:
                even = 1.0 / len(colors)
                mix = {c: even for c in colors}
            else:
                mix = {'C': 1.0}
        # Allocate counts per color
        allocations = {}
        remaining = need
        for i, (c, prop) in enumerate(mix.items()):
            count = int(round(prop * need))
            if i == len(mix) - 1:
                count = remaining  # force total to match
            allocations[c] = max(0, count)
            remaining -= allocations[c]
        # Add basics according to allocation
        for c, cnt in allocations.items():
            if cnt <= 0: continue
            name = _basic_for_color(c)
            basic = _make_basic_land(name)
            deck.add_card(basic, quantity=cnt)
    
    def _is_basic_land(self, card: Card) -> bool:
        return bool(card.type_line and 'Basic Land' in card.type_line)
    def _basic_for_color(self, color: str) -> str:
        return {
            'W': 'Plains',
            'U': 'Island',
            'B': 'Swamp',
            'R': 'Mountain',
            'G': 'Forest'
        }.get(color, 'Wastes')
    def _add_basic_lands(self, deck: Deck, count: int, colors: List[str]) -> None:
        if not colors:
            colors = ['C']
        # Spread basics across colors roughly evenly
        per_color = max(1, count // max(1, len(colors)))
        remaining = count
        for c in colors:
            if remaining <= 0: break
            to_add = min(per_color, remaining)
            name = self._basic_for_color(c)
            # find an actual card object in collection or synthesize a virtual basic
            basics = [card for card in self.collection
                    if card.name == name and self._is_basic_land(card)]
            if basics:
                deck.add_card(basics[0], quantity=to_add)
            else:
                # last-resort virtual basic; use _make_basic_land to ensure required fields
                deck.add_card(_make_basic_land(name), quantity=to_add)
            remaining -= to_add
        # Any remainder -> dump into first color
        if remaining > 0:
            name = self._basic_for_color(colors[0])
            basics = [card for card in self.collection
                    if card.name == name and self._is_basic_land(card)]
            if basics:
                deck.add_card(basics[0], quantity=remaining)
            else:
                deck.add_card(_make_basic_land(name), quantity=remaining)

    def _ensure_min_deck_size(self, deck: Deck, fmt: str, min_mainboard: int, card_pool: List[Card]) -> Deck:
        """Ensure deck mainboard has at least min_mainboard cards.

        Strategy:
        - Fill with available nonland cards from the card_pool (prefer new cards not already in deck).
        - If still short, add basic lands distributed by deck colors.
        - Respect commander singleton behavior (don't add duplicates in commander mainboard).
        """
        try:
            current_mb = sum(dc.quantity for dc in deck.get_mainboard_cards())
            if current_mb >= min_mainboard:
                return deck

            need = min_mainboard - current_mb

            # Build a set of existing mainboard non-commander ids
            existing_ids = {dc.card.id for dc in deck.get_mainboard_cards() if not dc.is_commander}
            is_commander = fmt == 'commander'

            # Prefer nonlands from the provided pool
            for card in card_pool:
                if need <= 0:
                    break
                if card.is_land():
                    continue
                if is_commander and card.id in existing_ids:
                    continue
                # Add one copy (safe and conservative)
                deck.add_card(card, quantity=1)
                existing_ids.add(card.id)
                need -= 1

            # If still need cards, add basics
            if need > 0:
                colors = deck.get_colors() or []
                # If commander and no commander present, try to preserve behavior
                if is_commander and not deck.get_commander():
                    # nothing we can do here automatically; just add basics
                    pass
                self._add_basic_lands(deck, need, colors)

        except Exception as exc:
            # Keep generation robust — swallow issues here but log
            print(f"⚠️ _ensure_min_deck_size failed: {exc}")

        return deck
    def _enforce_availability(self, deck: Deck, ledger: Dict[int,int], format: str, colors: List[str]) -> Deck:
        """
        Clamp deck to not exceed availability_ledger.
        Non-basic cards:
        - Commander: drop if ledger <= 0 (singleton already applied)
        - Other formats: cap quantity to remaining ledger
        Fill shortages with basics (safe and unlimited).
        """
        is_commander = format.lower() == 'commander'
        # Count current mainboard size (excluding commander)
        commander_dc = deck.get_commander()
        mainboard = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]
        target = 99 if is_commander else sum(dc.quantity for dc in mainboard)  # keep size for non-commander
        pruned: List[DeckCard] = []
        used_local: Dict[int,int] = {}
        for dc in mainboard:
            card = dc.card
            if self._is_basic_land(card):
                pruned.append(dc)
                continue
            cid = getattr(card, 'id', None)
            allowed = ledger.get(cid, 0)
            taken = used_local.get(cid, 0)
            if is_commander:
                # already singleton; require at least 1 availability
                if allowed - taken >= 1:
                    pruned.append(DeckCard(card=card, quantity=1))
                    used_local[cid] = taken + 1
                else:
                    print(f"⛔ Removing unavailable card: {card.name}")
            else:
                # cap to min(requested, remaining)
                cap = max(0, allowed - taken)
                new_qty = min(dc.quantity, cap)
                if new_qty > 0:
                    pruned.append(DeckCard(card=card, quantity=new_qty))
                    used_local[cid] = taken + new_qty
                else:
                    print(f"⛔ Removing unavailable card: {card.name}")
        # Rebuild deck with pruned non-commander mainboard
        deck.cards = []
        if commander_dc:
            deck.cards.append(DeckCard(card=commander_dc.card, quantity=1, is_commander=True))
        for dc in pruned:
            deck.cards.append(dc)
        # Fill any shortage with basic lands for all formats (not just commander)
        current_size = sum(dc.quantity for dc in deck.get_mainboard_cards() if not dc.is_commander)
        if current_size < target:
            shortage = target - current_size
            print(f"🧩 Filling shortage with basics: {shortage}")
            self._add_basic_lands(deck, shortage, colors or deck.get_colors())
        return deck
    def _enforce_copy_limits(self, deck: Deck, max_copies: int, card_pool: List[Card], format: str = 'standard') -> Deck:
        """Ensure no non-basic card exceeds max_copies for the format. Fill any removed slots."""
        try:
            # Build new mainboard preserving basics and commanders
            commander_dc = deck.get_commander()
            main = [dc for dc in deck.get_mainboard_cards() if not dc.is_commander]

            new_main = []
            removed_slots = 0
            for dc in main:
                if self._is_basic_land(dc.card):
                    new_main.append(dc)
                    continue
                # Cap copies
                if dc.quantity > max_copies:
                    removed_slots += (dc.quantity - max_copies)
                    dc.quantity = max_copies
                if dc.quantity > 0:
                    new_main.append(dc)

            # Rebuild deck.cards
            deck.cards = []
            if commander_dc:
                deck.cards.append(DeckCard(card=commander_dc.card, quantity=1, is_commander=True))
            deck.cards.extend(new_main)

            # If we removed slots, try to fill with nonlands from pool
            if removed_slots > 0:
                existing_ids = {dc.card.id for dc in deck.get_mainboard_cards() if not dc.is_commander}
                for card in card_pool:
                    if removed_slots <= 0:
                        break
                    if card.is_land():
                        continue
                    if card.id in existing_ids:
                        continue
                    deck.add_card(card, quantity=1)
                    existing_ids.add(card.id)
                    removed_slots -= 1

                # If still need slots, add basics
                if removed_slots > 0:
                    colors = deck.get_colors() or []
                    self._add_basic_lands(deck, removed_slots, colors)

        except Exception as exc:
            print(f"⚠️ _enforce_copy_limits failed: {exc}")
        return deck