import sys
import pytest
sys.path.insert(0, '.')

from src.ai.deck_generator import DeckGenerator
from src.models.card import Card

class FastDeckGenerator(DeckGenerator):
    """Small GA replacement for fast, deterministic tests."""
    def _genetic_algorithm(self, card_pool, archetype, deck_size, format, commander):
        # return a few sampled random decks and pick best via evaluator
        samples = []
        for _ in range(4):
            d = self._create_random_deck(card_pool, archetype, deck_size, format, commander)
            samples.append((self._evaluate_deck(d, archetype), d))
        samples.sort(key=lambda x: -x[0])
        return samples[0][1]


def build_basic_collection(with_legendary_commander=False):
    collection = []
    # 40 unique nonland cards
    for i in range(40):
        collection.append(Card(
            id=1000 + i,
            name=f"TestCard{i}",
            set_code='TST',
            collector_number=str(i),
            rarity='common',
            mana_cost='{R}',
            cmc=1.0,
            colors='R',
            color_identity='R',
            type_line='Creature',
            card_types='Creature',
            subtypes='Goblin',
            oracle_text='',
            quantity=4
        ))
    # add some nonbasic lands
    for j in range(6):
        collection.append(Card(id=3000+j, name=f"Land{j}", set_code='L', collector_number=str(j), rarity='rare', mana_cost='', cmc=0.0, colors='', color_identity='R', type_line='Land', card_types='Land', subtypes='Plains', oracle_text='', quantity=4))
    # add basics
    collection.append(Card(id=2000, name='Mountain', set_code='M', collector_number='1', rarity='common', mana_cost='', cmc=0.0, colors='', color_identity='R', type_line='Basic Land — Mountain', card_types='Land,Basic', subtypes='Mountain', oracle_text='({T}: Add {R}.)', quantity=20))

    if with_legendary_commander:
        # add a legendary creature commander
        collection.append(Card(id=4000, name='LegendLord', set_code='LG', collector_number='1', rarity='rare', mana_cost='{1}{R}', cmc=2.0, colors='R', color_identity='R', type_line='Legendary Creature — Human', card_types='Creature,Legendary', subtypes='Lord', oracle_text='', quantity=1))
    return collection


def test_standard_deck_is_valid():
    collection = build_basic_collection()
    gen = FastDeckGenerator(collection)
    deck = gen.generate_deck(archetype='aggro', format='standard', colors=['R'], deck_size=60)

    assert deck.mainboard_count() >= 60
    errs = deck.validate()
    assert errs == [], f"Standard deck validation errors: {errs}"


def test_commander_deck_has_commander_and_100_cards():
    collection = build_basic_collection(with_legendary_commander=True)
    gen = FastDeckGenerator(collection)
    deck = gen.generate_deck(archetype='aggro', format='commander', colors=['R'], deck_size=99)

    # Commander format expects 100 total including commander; Deck.mainboard_count counts all mainboard cards
    assert deck.mainboard_count() == 100
    assert deck.get_commander() is not None
    errs = deck.validate()
    assert errs == [], f"Commander deck validation errors: {errs}"


def test_availability_backfill_fills_to_minimum():
    # Build collection but set availability ledger to zero for non-basics
    collection = build_basic_collection()
    # ledger makes non-basics unavailable (except basics)
    ledger = {c.id: (0 if not (c.type_line and 'Basic Land' in c.type_line) else 999) for c in collection}

    gen = FastDeckGenerator(collection)
    deck = gen.generate_deck(archetype='midrange', format='standard', colors=['R'], deck_size=60, availability_ledger=ledger)

    assert deck.mainboard_count() >= 60
    errs = deck.validate()
    assert errs == [], f"Availability backfill produced invalid deck: {errs}"
