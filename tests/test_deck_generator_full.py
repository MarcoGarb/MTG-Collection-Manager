import sys
import time
from pathlib import Path
import pytest
sys.path.insert(0, '.')

from src.data.database import DatabaseManager
from src.ai.deck_generator import DeckGenerator

DB_PATH = Path('data/collection.db')

@pytest.mark.skipif(not DB_PATH.exists(), reason="No data/collection.db found in workspace")
def test_full_ga_on_real_collection():
    """Integration test: run the full GA on the real collection DB.

    This test is intentionally integration-level and may take a while depending
    on your machine and collection size. It will be skipped if `data/collection.db` is missing.
    """
    db = DatabaseManager(str(DB_PATH))
    db.connect()
    try:
        collection = db.get_all_cards()
    finally:
        db.disconnect()

    assert collection, "Collection is empty in DB"

    gen = DeckGenerator(collection)

    # Run a full GA for a standard deck (this may be slow)
    start = time.time()
    deck = gen.generate_deck(archetype='midrange', format='standard', colors=['R'], deck_size=60)
    duration = time.time() - start
    print(f"Full GA finished in {duration:.1f}s; mainboard={deck.mainboard_count()}")

    # Verify deck meets format minima
    min_cards = deck.FORMAT_RULES.get('standard', {}).get('min_cards', 60)
    assert deck.mainboard_count() >= min_cards
    errs = deck.validate()
    assert errs == [], f"Generated deck invalid: {errs}"

    # Try commander (auto-select commander if possible)
    start = time.time()
    cmd = gen.generate_deck(archetype='midrange', format='commander', colors=['R'], deck_size=99, auto_select_commander=True)
    duration = time.time() - start
    print(f"Commander GA finished in {duration:.1f}s; mainboard={cmd.mainboard_count()}, commander={bool(cmd.get_commander())}")

    # Commander must have commander and 100 cards
    assert cmd.get_commander() is not None, "Commander auto-selection failed (no commander in generated deck)"
    assert cmd.mainboard_count() >= 100
    errs2 = cmd.validate()
    assert errs2 == [], f"Generated commander deck invalid: {errs2}"
