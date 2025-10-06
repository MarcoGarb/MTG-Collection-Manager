"""
Test script to verify CSV import and database operations.
"""
from src.data.database import DatabaseManager
from src.data.importer import CSVImporter


def main():
    print("=" * 60)
    print("MTG Collection Manager - Data Import Test")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager()
    db.initialize_schema()
    
    # Check CSV columns
    print("\n2. Checking CSV structure...")
    csv_path = "data/all cards.csv"
    columns = CSVImporter.detect_columns(csv_path)
    print(f"CSV Columns: {columns}")
    
    # Import cards
    print("\n3. Importing cards from CSV...")
    cards = CSVImporter.import_from_manabox(csv_path)
    print(f"✓ Imported {len(cards)} cards")
    
    # Show first few cards
    print("\n4. Sample cards:")
    for card in cards[:5]:
        print(f"  - {card}")
    
    # Save to database
    print("\n5. Saving to database...")
    db.connect()
    db.clear_collection()  # Clear any existing data
    
    for card in cards:
        db.add_card(card)
    
    db.disconnect()
    print(f"✓ Saved {len(cards)} cards to database")
    
    # Get statistics
    print("\n6. Collection statistics:")
    db.connect()
    stats = db.get_collection_stats()
    print(f"  Total cards: {stats['total_cards']}")
    print(f"  Unique cards: {stats['unique_cards']}")
    print(f"  Total value: ${stats['total_value']:.2f}")
    print(f"  By rarity: {stats['by_rarity']}")
    db.disconnect()
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Ready to build the UI.")
    print("=" * 60)


if __name__ == "__main__":
    main()