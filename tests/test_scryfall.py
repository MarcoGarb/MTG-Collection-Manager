"""
Test Scryfall API integration.
"""
from src.api.scryfall import ScryfallAPI

api = ScryfallAPI()

print("Testing Scryfall API...")
print("=" * 60)

# Test 1: Fetch by set and number
print("\n1. Testing fetch by set and collector number:")
card = api.get_card_by_set_and_number("jud", "104")  # Anurid Barkripper from your collection
if card:
    print(f"✓ Found: {card['name']}")
    print(f"  Set: {card['set'].upper()} #{card['collector_number']}")
    print(f"  Price: ${api.extract_price_from_card(card)}")
else:
    print("✗ Card not found")

# Test 2: Fetch by name
print("\n2. Testing fetch by name:")
card = api.get_card_by_name("Lightning Bolt")
if card:
    print(f"✓ Found: {card['name']}")
    print(f"  Latest printing: {card['set'].upper()}")
    print(f"  Price: ${api.extract_price_from_card(card)}")
else:
    print("✗ Card not found")

print("\n" + "=" * 60)
print("✓ Scryfall API tests complete!")