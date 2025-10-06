"""
Test AI deck generator.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.card import Card
from src.ai.deck_generator import DeckGenerator
from src.ai.deck_analyzer import DeckAnalyzer


def create_test_collection():
    """Create a test collection of cards."""
    cards = []
    
    # Red creatures (aggro)
    cards.append(Card(
        id='goblin-guide',
        name='Goblin Guide',
        set_code='ZEN',
        collector_number='95',
        mana_cost='{R}',
        cmc=1.0,
        colors='R',
        type_line='Creature — Goblin Scout',
        oracle_text='Haste. Whenever Goblin Guide attacks, defending player reveals the top card of their library. 2/2'
    ))
    
    cards.append(Card(
        id='monastery-swiftspear',
        name='Monastery Swiftspear',
        set_code='KTK',
        collector_number='118',
        mana_cost='{R}',
        cmc=1.0,
        colors='R',
        type_line='Creature — Human Monk',
        oracle_text='Haste. Prowess (Whenever you cast a noncreature spell, this creature gets +1/+1 until end of turn.) 1/2'
    ))
    
    cards.append(Card(
        id='burning-tree-emissary',
        name='Burning-Tree Emissary',
        set_code='GTC',
        collector_number='216',
        mana_cost='{R}{G}',
        cmc=2.0,
        colors='RG',
        type_line='Creature — Human Shaman',
        oracle_text='When Burning-Tree Emissary enters the battlefield, add {R}{G}. 2/2'
    ))
    
    cards.append(Card(
        id='lightning-bolt',
        name='Lightning Bolt',
        set_code='M11',
        collector_number='146',
        mana_cost='{R}',
        cmc=1.0,
        colors='R',
        type_line='Instant',
        oracle_text='Lightning Bolt deals 3 damage to any target.'
    ))
    
    cards.append(Card(
        id='shock',
        name='Shock',
        set_code='M21',
        collector_number='159',
        mana_cost='{R}',
        cmc=1.0,
        colors='R',
        type_line='Instant',
        oracle_text='Shock deals 2 damage to any target.'
    ))
    
    cards.append(Card(
        id='lava-spike',
        name='Lava Spike',
        set_code='CHK',
        collector_number='178',
        mana_cost='{R}',
        cmc=1.0,
        colors='R',
        type_line='Sorcery',
        oracle_text='Lava Spike deals 3 damage to target player or planeswalker.'
    ))
    
    # More creatures at different CMCs
    for i in range(8):
        cards.append(Card(
            id=f'red-creature-2-{i}',
            name=f'Ember Warrior {i}',
            set_code='TST',
            collector_number=f'{100+i}',
            mana_cost='{1}{R}',
            cmc=2.0,
            colors='R',
            type_line='Creature — Goblin Warrior',
            oracle_text='Haste. 2/1'
        ))
    
    for i in range(8):
        cards.append(Card(
            id=f'red-creature-3-{i}',
            name=f'Fire Beast {i}',
            set_code='TST',
            collector_number=f'{110+i}',
            mana_cost='{2}{R}',
            cmc=3.0,
            colors='R',
            type_line='Creature — Beast',
            oracle_text='Trample. 3/2'
        ))
    
    for i in range(5):
        cards.append(Card(
            id=f'red-creature-4-{i}',
            name=f'Flame Dragon {i}',
            set_code='TST',
            collector_number=f'{120+i}',
            mana_cost='{3}{R}',
            cmc=4.0,
            colors='R',
            type_line='Creature — Dragon',
            oracle_text='Flying, haste. 4/3'
        ))
    
    for i in range(3):
        cards.append(Card(
            id=f'red-creature-5-{i}',
            name=f'Inferno Titan {i}',
            set_code='TST',
            collector_number=f'{130+i}',
            mana_cost='{4}{R}',
            cmc=5.0,
            colors='R',
            type_line='Creature — Giant',
            oracle_text='When this creature enters the battlefield, it deals 3 damage divided as you choose among any number of targets. 5/4'
        ))
    
    # Removal spells
    cards.append(Card(
        id='abrade',
        name='Abrade',
        set_code='AKH',
        collector_number='136',
        mana_cost='{1}{R}',
        cmc=2.0,
        colors='R',
        type_line='Instant',
        oracle_text='Choose one — Abrade deals 3 damage to target creature; or destroy target artifact.'
    ))
    
    cards.append(Card(
        id='bonecrusher-giant',
        name='Bonecrusher Giant',
        set_code='ELD',
        collector_number='115',
        mana_cost='{2}{R}',
        cmc=3.0,
        colors='R',
        type_line='Creature — Giant',
        oracle_text='Whenever Bonecrusher Giant becomes the target of a spell, Bonecrusher Giant deals 2 damage to that spell\'s controller. 4/3'
    ))
    
    cards.append(Card(
        id='fire-blast',
        name='Fire Blast',
        set_code='VIS',
        collector_number='79',
        mana_cost='{4}{R}{R}',
        cmc=6.0,
        colors='R',
        type_line='Instant',
        oracle_text='You may sacrifice two Mountains rather than pay this spell\'s mana cost. Fire Blast deals 4 damage to any target.'
    ))
    
    # Card draw
    cards.append(Card(
        id='light-up-the-stage',
        name='Light Up the Stage',
        set_code='RNA',
        collector_number='107',
        mana_cost='{2}{R}',
        cmc=3.0,
        colors='R',
        type_line='Sorcery',
        oracle_text='Spectacle {R}. Exile the top two cards of your library. Until the end of your next turn, you may play those cards.'
    ))
    
    cards.append(Card(
        id='experimental-frenzy',
        name='Experimental Frenzy',
        set_code='GRN',
        collector_number='99',
        mana_cost='{3}{R}',
        cmc=4.0,
        colors='R',
        type_line='Enchantment',
        oracle_text='You may look at the top card of your library any time. You may play the top card of your library. You can\'t play cards from your hand.'
    ))
    
    cards.append(Card(
        id='thrill-of-possibility',
        name='Thrill of Possibility',
        set_code='ELD',
        collector_number='146',
        mana_cost='{1}{R}',
        cmc=2.0,
        colors='R',
        type_line='Instant',
        oracle_text='As an additional cost to cast this spell, discard a card. Draw two cards.'
    ))
    
    # Lands - FIXED F-STRING SYNTAX
    for i in range(30):
        cards.append(Card(
            id=f'mountain-{i}',
            name='Mountain',
            set_code='M21',
            collector_number=f'{270 + i}',  # FIXED
            mana_cost='',
            cmc=0.0,
            colors='',
            type_line='Basic Land — Mountain',
            oracle_text='({T}: Add {R}.)'
        ))
    
    cards.append(Card(
        id='sunbaked-canyon',
        name='Sunbaked Canyon',
        set_code='MH1',
        collector_number='247',
        mana_cost='',
        cmc=0.0,
        colors='',
        type_line='Land',
        oracle_text='{T}, Pay 1 life: Add {R} or {W}.'
    ))
    
    cards.append(Card(
        id='castle-embereth',
        name='Castle Embereth',
        set_code='ELD',
        collector_number='239',
        mana_cost='',
        cmc=0.0,
        colors='',
        type_line='Land',
        oracle_text='{T}: Add {R}. {1}{R}{R}, {T}: Creatures you control get +1/+0 until end of turn.'
    ))
    
    # White cards for RW aggro
    cards.append(Card(
        id='thalia-guardian',
        name='Thalia, Guardian of Thraben',
        set_code='DKA',
        collector_number='24',
        mana_cost='{1}{W}',
        cmc=2.0,
        colors='W',
        type_line='Legendary Creature — Human Soldier',
        oracle_text='First strike. Noncreature spells cost {1} more to cast. 2/1'
    ))
    
    cards.append(Card(
        id='elite-vanguard',
        name='Elite Vanguard',
        set_code='M10',
        collector_number='8',
        mana_cost='{W}',
        cmc=1.0,
        colors='W',
        type_line='Creature — Human Soldier',
        oracle_text='2/1'
    ))
    
    cards.append(Card(
        id='savannah-lions',
        name='Savannah Lions',
        set_code='M10',
        collector_number='33',
        mana_cost='{W}',
        cmc=1.0,
        colors='W',
        type_line='Creature — Cat',
        oracle_text='2/1'
    ))
    
    for i in range(8):
        cards.append(Card(
            id=f'white-creature-{i}',
            name=f'White Knight {i}',
            set_code='TST',
            collector_number=f'{200 + i}',  # FIXED
            mana_cost='{1}{W}',
            cmc=2.0,
            colors='W',
            type_line='Creature — Human Knight',
            oracle_text='First strike. 2/2'
        ))
    
    for i in range(5):
        cards.append(Card(
            id=f'white-creature-3-{i}',
            name=f'Angel Soldier {i}',
            set_code='TST',
            collector_number=f'{210 + i}',  # FIXED
            mana_cost='{2}{W}',
            cmc=3.0,
            colors='W',
            type_line='Creature — Angel',
            oracle_text='Flying. 2/3'
        ))
    
    cards.append(Card(
        id='swords-to-plowshares',
        name='Swords to Plowshares',
        set_code='ICE',
        collector_number='53',
        mana_cost='{W}',
        cmc=1.0,
        colors='W',
        type_line='Instant',
        oracle_text='Exile target creature. Its controller gains life equal to its power.'
    ))
    
    cards.append(Card(
        id='path-to-exile',
        name='Path to Exile',
        set_code='CON',
        collector_number='15',
        mana_cost='{W}',
        cmc=1.0,
        colors='W',
        type_line='Instant',
        oracle_text='Exile target creature. Its controller may search their library for a basic land card, put it onto the battlefield tapped, then shuffle.'
    ))
    
    for i in range(30):
        cards.append(Card(
            id=f'plains-{i}',
            name='Plains',
            set_code='M21',
            collector_number=f'{260 + i}',  # FIXED
            mana_cost='',
            cmc=0.0,
            colors='',
            type_line='Basic Land — Plains',
            oracle_text='({T}: Add {W}.)'
        ))
    
    # Blue control cards
    cards.append(Card(
        id='counterspell',
        name='Counterspell',
        set_code='ICE',
        collector_number='64',
        mana_cost='{U}{U}',
        cmc=2.0,
        colors='U',
        type_line='Instant',
        oracle_text='Counter target spell.'
    ))
    
    cards.append(Card(
        id='supreme-verdict',
        name='Supreme Verdict',
        set_code='RTR',
        collector_number='201',
        mana_cost='{1}{W}{W}{U}',
        cmc=4.0,
        colors='WU',
        type_line='Sorcery',
        oracle_text='This spell can\'t be countered. Destroy all creatures.'
    ))
    
    cards.append(Card(
        id='sphinx-revelation',
        name='Sphinx\'s Revelation',
        set_code='RTR',
        collector_number='200',
        mana_cost='{X}{W}{U}{U}',
        cmc=3.0,
        colors='WU',
        type_line='Instant',
        oracle_text='You gain X life and draw X cards.'
    ))
    
    cards.append(Card(
        id='wrath-of-god',
        name='Wrath of God',
        set_code='M10',
        collector_number='36',
        mana_cost='{2}{W}{W}',
        cmc=4.0,
        colors='W',
        type_line='Sorcery',
        oracle_text='Destroy all creatures. They can\'t be regenerated.'
    ))
    
    cards.append(Card(
        id='mana-leak',
        name='Mana Leak',
        set_code='M12',
        collector_number='63',
        mana_cost='{1}{U}',
        cmc=2.0,
        colors='U',
        type_line='Instant',
        oracle_text='Counter target spell unless its controller pays {3}.'
    ))
    
    for i in range(30):
        cards.append(Card(
            id=f'island-{i}',
            name='Island',
            set_code='M21',
            collector_number=f'{330 + i}',  # FIXED
            mana_cost='',
            cmc=0.0,
            colors='',
            type_line='Basic Land — Island',
            oracle_text='({T}: Add {U}.)'
        ))
    
    for i in range(10):
        cards.append(Card(
            id=f'blue-control-{i}',
            name=f'Cancel Variant {i}',
            set_code='TST',
            collector_number=f'{300 + i}',  # FIXED
            mana_cost='{2}{U}',
            cmc=3.0,
            colors='U',
            type_line='Instant',
            oracle_text='Counter target spell unless its controller pays {3}.'
        ))
    
    for i in range(5):
        cards.append(Card(
            id=f'blue-draw-{i}',
            name=f'Divination Variant {i}',
            set_code='TST',
            collector_number=f'{310 + i}',  # FIXED
            mana_cost='{2}{U}',
            cmc=3.0,
            colors='U',
            type_line='Sorcery',
            oracle_text='Draw two cards.'
        ))
    
    # Green cards
    cards.append(Card(
        id='llanowar-elves',
        name='Llanowar Elves',
        set_code='M19',
        collector_number='314',
        mana_cost='{G}',
        cmc=1.0,
        colors='G',
        type_line='Creature — Elf Druid',
        oracle_text='{T}: Add {G}. 1/1'
    ))
    
    cards.append(Card(
        id='cultivate',
        name='Cultivate',
        set_code='M11',
        collector_number='168',
        mana_cost='{2}{G}',
        cmc=3.0,
        colors='G',
        type_line='Sorcery',
        oracle_text='Search your library for up to two basic land cards, reveal those cards, put one onto the battlefield tapped and the other into your hand, then shuffle.'
    ))
    
    cards.append(Card(
        id='rampant-growth',
        name='Rampant Growth',
        set_code='M12',
        collector_number='193',
        mana_cost='{1}{G}',
        cmc=2.0,
        colors='G',
        type_line='Sorcery',
        oracle_text='Search your library for a basic land card, put that card onto the battlefield tapped, then shuffle.'
    ))
    
    for i in range(30):
        cards.append(Card(
            id=f'forest-{i}',
            name='Forest',
            set_code='M21',
            collector_number=f'{400 + i}',  # FIXED
            mana_cost='',
            cmc=0.0,
            colors='',
            type_line='Basic Land — Forest',
            oracle_text='({T}: Add {G}.)'
        ))
    
    for i in range(8):
        cards.append(Card(
            id=f'green-creature-{i}',
            name=f'Grizzly Bear {i}',
            set_code='TST',
            collector_number=f'{400 + i}',  # FIXED
            mana_cost='{1}{G}',
            cmc=2.0,
            colors='G',
            type_line='Creature — Bear',
            oracle_text='2/2'
        ))
    
    # Multi-color lands
    cards.append(Card(
        id='sacred-foundry',
        name='Sacred Foundry',
        set_code='GTC',
        collector_number='245',
        mana_cost='',
        cmc=0.0,
        colors='',
        type_line='Land — Mountain Plains',
        oracle_text='({T}: Add {R} or {W}.) As Sacred Foundry enters the battlefield, you may pay 2 life. If you don\'t, it enters the battlefield tapped.'
    ))
    
    cards.append(Card(
        id='hallowed-fountain',
        name='Hallowed Fountain',
        set_code='RTR',
        collector_number='241',
        mana_cost='',
        cmc=0.0,
        colors='',
        type_line='Land — Plains Island',
        oracle_text='({T}: Add {W} or {U}.) As Hallowed Fountain enters the battlefield, you may pay 2 life. If you don\'t, it enters the battlefield tapped.'
    ))
    
    cards.append(Card(
        id='stomping-ground',
        name='Stomping Ground',
        set_code='GTC',
        collector_number='247',
        mana_cost='',
        cmc=0.0,
        colors='',
        type_line='Land — Mountain Forest',
        oracle_text='({T}: Add {R} or {G}.) As Stomping Ground enters the battlefield, you may pay 2 life. If you don\'t, it enters the battlefield tapped.'
    ))
    
    # Artifacts
    cards.append(Card(
        id='sol-ring',
        name='Sol Ring',
        set_code='C14',
        collector_number='264',
        mana_cost='{1}',
        cmc=1.0,
        colors='',
        type_line='Artifact',
        oracle_text='{T}: Add {C}{C}.'
    ))
    
    cards.append(Card(
        id='arcane-signet',
        name='Arcane Signet',
        set_code='ELD',
        collector_number='331',
        mana_cost='{2}',
        cmc=2.0,
        colors='',
        type_line='Artifact',
        oracle_text='{T}: Add one mana of any color in your commander\'s color identity.'
    ))
    
    cards.append(Card(
        id='mind-stone',
        name='Mind Stone',
        set_code='WTH',
        collector_number='153',
        mana_cost='{2}',
        cmc=2.0,
        colors='',
        type_line='Artifact',
        oracle_text='{T}: Add {C}. {1}, {T}, Sacrifice Mind Stone: Draw a card.'
    ))
    
    return cards

def test_generate_aggro_deck():
    """Test generating an aggro deck."""
    print("\n" + "="*60)
    print("TEST: Generate Aggro Deck")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate mono-red aggro
    deck = generator.generate_deck(
        archetype='aggro',
        format='standard',
        colors=['R'],
        deck_size=60
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    print(f"   Format: {deck.format}")
    print(f"   Total cards: {len(deck.get_mainboard_cards()) if hasattr(deck, 'get_mainboard_cards') else 'N/A'}")
    
    # Analyze the deck
    analyzer = DeckAnalyzer(deck)
    analysis = analyzer.analyze_deck()
    
    # Count total cards from mainboard
    total_cards = sum(dc.quantity for dc in deck.get_mainboard_cards())
    
    print(f"\n📊 Deck Analysis:")
    print(f"   Total Cards: {total_cards}")
    print(f"   Colors: {analysis['colors']}")
    print(f"   Creatures: {analysis['card_types'].get('creature', 0)}")
    print(f"   Removal: {analysis['removal_count']}")
    print(f"   Card Draw: {analysis['card_draw_count']}")
    
    print(f"\n📈 Mana Curve:")
    for cmc in sorted(analysis['mana_curve'].keys()):
        count = analysis['mana_curve'][cmc]
        print(f"   CMC {cmc}: {'█' * count} ({count})")
    
    print(f"\n🎯 Themes:")
    for theme, count in sorted(analysis['themes'].items(), key=lambda x: -x[1])[:5]:
        print(f"   {theme}: {count}")
    
    # Print sample cards
    print(f"\n📋 Sample Cards:")
    mainboard = deck.get_mainboard_cards()
    for dc in mainboard[:15]:  # Show first 15 cards
        print(f"   {dc.quantity}x {dc.card.name} ({dc.card.mana_cost or 'Land'})")
    
    return deck


def test_generate_control_deck():
    """Test generating a control deck."""
    print("\n" + "="*60)
    print("TEST: Generate Control Deck")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate UW control
    deck = generator.generate_deck(
        archetype='control',
        format='standard',
        colors=['W', 'U'],
        deck_size=60
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    print(f"   Format: {deck.format}")
    
    # Analyze the deck
    analyzer = DeckAnalyzer(deck)
    analysis = analyzer.analyze_deck()
    
    # Count total cards from mainboard
    total_cards = sum(dc.quantity for dc in deck.get_mainboard_cards())
    
    print(f"\n📊 Deck Analysis:")
    print(f"   Total Cards: {total_cards}")
    print(f"   Colors: {analysis['colors']}")
    print(f"   Creatures: {analysis['card_types'].get('creature', 0)}")
    print(f"   Removal: {analysis['removal_count']}")
    print(f"   Card Draw: {analysis['card_draw_count']}")
    
    print(f"\n📈 Mana Curve:")
    for cmc in sorted(analysis['mana_curve'].keys()):
        count = analysis['mana_curve'][cmc]
        print(f"   CMC {cmc}: {'█' * count} ({count})")
    
    print(f"\n📋 Sample Cards:")
    mainboard = deck.get_mainboard_cards()
    for dc in mainboard[:15]:
        print(f"   {dc.quantity}x {dc.card.name} ({dc.card.mana_cost or 'Land'})")
    
    return deck


def test_generate_midrange_deck():
    """Test generating a midrange deck."""
    print("\n" + "="*60)
    print("TEST: Generate Midrange Deck")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate RG midrange
    deck = generator.generate_deck(
        archetype='midrange',
        format='modern',
        colors=['R', 'G'],
        deck_size=60
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    print(f"   Format: {deck.format}")
    
    # Analyze the deck
    analyzer = DeckAnalyzer(deck)
    analysis = analyzer.analyze_deck()
    
    # Count total cards from mainboard
    total_cards = sum(dc.quantity for dc in deck.get_mainboard_cards())
    
    print(f"\n📊 Deck Analysis:")
    print(f"   Total Cards: {total_cards}")
    print(f"   Colors: {analysis['colors']}")
    print(f"   Creatures: {analysis['card_types'].get('creature', 0)}")
    print(f"   Removal: {analysis['removal_count']}")
    print(f"   Threats: {analysis['threats_count']}")
    print(f"   Answers: {analysis['answers_count']}")
    
    print(f"\n📈 Mana Curve:")
    for cmc in sorted(analysis['mana_curve'].keys()):
        count = analysis['mana_curve'][cmc]
        print(f"   CMC {cmc}: {'█' * count} ({count})")
    
    return deck


def test_compare_archetypes():
    """Compare different archetype generations."""
    print("\n" + "="*60)
    print("TEST: Compare All Archetypes")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    archetypes = ['aggro', 'midrange', 'control', 'combo']
    results = {}
    
    for archetype in archetypes:
        print(f"\nGenerating {archetype}...")
        deck = generator.generate_deck(
            archetype=archetype,
            format='standard',
            colors=['R'],
            deck_size=60
        )
        
        analyzer = DeckAnalyzer(deck)
        analysis = analyzer.analyze_deck()
        
        results[archetype] = {
            'deck': deck,
            'analysis': analysis
        }
    
    # Print comparison table
    print("\n" + "="*60)
    print("COMPARISON TABLE")
    print("="*60)
    print(f"{'Archetype':<12} {'Total':<8} {'Creatures':<12} {'Removal':<10} {'Avg CMC':<10}")
    print("-" * 60)
    
    for archetype, data in results.items():
        deck = data['deck']
        analysis = data['analysis']
        creatures = analysis['card_types'].get('creature', 0)
        removal = analysis['removal_count']
        
        # Calculate total cards
        total_cards = sum(dc.quantity for dc in deck.get_mainboard_cards())
        
        # Calculate average CMC
        curve = analysis['mana_curve']
        total_nonland = sum(curve.values())
        avg_cmc = sum(cmc * count for cmc, count in curve.items()) / total_nonland if total_nonland > 0 else 0
        
        print(f"{archetype:<12} {total_cards:<8} {creatures:<12} {removal:<10} {avg_cmc:<10.2f}")
    
    return results

def test_generate_commander_deck_with_auto_selection():
    """Test Commander deck generation with automatic commander selection."""
    print("\n" + "="*60)
    print("TEST: Generate Commander Deck (Auto-Select Commander)")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Gruul (R/G) Commander deck with auto-selection
    deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=['R', 'G'],
        deck_size=99,  # Will be adjusted automatically
        commander=None,  # Let it auto-select
        auto_select_commander=True
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    print(f"   Format: {deck.format}")
    
    # Get commander
    commander_dc = deck.get_commander()
    
    # Validate commander
    print(f"\n👑 Commander Validation:")
    if commander_dc:
        print(f"   ✅ Commander: {commander_dc.card.name}")
        print(f"   Type: {commander_dc.card.type_line}")
        print(f"   Colors: {commander_dc.card.color_identity}")
        
        # Check if legendary creature
        assert 'Legendary' in commander_dc.card.type_line, "Commander must be legendary"
        assert 'Creature' in commander_dc.card.type_line, "Commander must be a creature"
        print(f"   ✅ Is Legendary Creature: True")
        
        # Check quantity
        assert commander_dc.quantity == 1, "Commander must have quantity of 1"
        print(f"   ✅ Quantity: {commander_dc.quantity}")
    else:
        print(f"   ⚠️ No commander found!")
    
    # Validate deck size
    mainboard = deck.get_mainboard_cards()
    total_mainboard = sum(dc.quantity for dc in mainboard if not dc.is_commander)
    
    print(f"\n📦 Deck Size Validation:")
    print(f"   Mainboard (excluding commander): {total_mainboard}")
    print(f"   Commander: {1 if commander_dc else 0}")
    print(f"   Total: {total_mainboard + (1 if commander_dc else 0)}")
    
    expected_total = 100
    actual_total = total_mainboard + (1 if commander_dc else 0)
    if actual_total == expected_total:
        print(f"   ✅ Deck size is correct: {actual_total}/100")
    else:
        print(f"   ⚠️ Deck size mismatch: {actual_total}/100")
    
    # Validate singleton rule (except basic lands)
    print(f"\n🎯 Singleton Rule Validation:")
    card_counts = {}
    violations = []
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_name = dc.card.name
        is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line
        
        if card_name not in card_counts:
            card_counts[card_name] = 0
        card_counts[card_name] += dc.quantity
        
        # Check singleton (except basic lands)
        if not is_basic and dc.quantity > 1:
            violations.append(f"{card_name}: {dc.quantity} copies")
    
    if violations:
        print(f"   ❌ Singleton violations found:")
        for v in violations:
            print(f"      {v}")
    else:
        print(f"   ✅ All non-basic cards are singleton")
    
    # Validate color identity
    print(f"\n🎨 Color Identity Validation:")
    commander_colors = set(commander_dc.card.get_color_identity_list()) if commander_dc else set()
    print(f"   Commander color identity: {commander_colors}")
    
    color_violations = []
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_colors = set(dc.card.get_color_identity_list())
        if not card_colors.issubset(commander_colors):
            color_violations.append(f"{dc.card.name}: {card_colors} (not in {commander_colors})")
    
    if color_violations:
        print(f"   ❌ Color identity violations:")
        for v in color_violations[:5]:  # Show first 5
            print(f"      {v}")
    else:
        print(f"   ✅ All cards match commander color identity")
    
    # Analyze deck
    analyzer = DeckAnalyzer(deck)
    analysis = analyzer.analyze_deck()
    
    print(f"\n📊 Deck Analysis:")
    print(f"   Colors: {analysis['colors']}")
    print(f"   Creatures: {analysis['card_types'].get('creature', 0)}")
    print(f"   Removal: {analysis['removal_count']}")
    print(f"   Ramp: {analysis['ramp_count']}")
    print(f"   Card Draw: {analysis['card_draw_count']}")
    
    print(f"\n📈 Mana Curve:")
    for cmc in sorted(analysis['mana_curve'].keys()):
        count = analysis['mana_curve'][cmc]
        bar = '█' * min(count, 50)  # Cap display at 50
        print(f"   CMC {cmc}: {bar} ({count})")
    
    print(f"\n🎯 Top Themes:")
    for theme, count in sorted(analysis['themes'].items(), key=lambda x: -x[1])[:5]:
        print(f"   {theme}: {count}")
    
    print(f"\n📋 Sample Cards (first 20):")
    for dc in mainboard[:20]:
        if dc.is_commander:
            print(f"   👑 {dc.quantity}x {dc.card.name} (COMMANDER)")
        else:
            print(f"   {dc.quantity}x {dc.card.name} ({dc.card.mana_cost or 'Land'})")
    
    return deck


def test_generate_commander_deck_with_manual_commander():
    """Test Commander deck generation with manually specified commander."""
    print("\n" + "="*60)
    print("TEST: Generate Commander Deck (Manual Commander)")
    print("="*60)
    
    collection = create_test_collection()
    
    # Find a suitable commander from collection
    suitable_commanders = [
        c for c in collection
        if c.type_line and 'Legendary Creature' in c.type_line
    ]
    
    if not suitable_commanders:
        print("   ⚠️ No legendary creatures in test collection, skipping test")
        return None
    
    # Pick first suitable commander
    chosen_commander = suitable_commanders[0]
    commander_colors = chosen_commander.get_color_identity_list()
    
    print(f"\n👑 Chosen Commander:")
    print(f"   Name: {chosen_commander.name}")
    print(f"   Type: {chosen_commander.type_line}")
    print(f"   Colors: {commander_colors}")
    print(f"   CMC: {chosen_commander.cmc}")
    
    generator = DeckGenerator(collection)
    
    # Generate deck with specified commander
    deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=commander_colors,
        commander=chosen_commander,
        auto_select_commander=False
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    
    # Validate commander matches
    commander_dc = deck.get_commander()
    
    print(f"\n🔍 Commander Verification:")
    if commander_dc:
        matches = commander_dc.card.name == chosen_commander.name
        print(f"   Commander in deck: {commander_dc.card.name}")
        print(f"   Expected: {chosen_commander.name}")
        print(f"   ✅ Match: {matches}")
        
        assert matches, f"Commander mismatch: expected {chosen_commander.name}, got {commander_dc.card.name}"
    else:
        print(f"   ❌ No commander found in deck!")
        assert False, "Commander not found in generated deck"
    
    # Validate deck
    mainboard = deck.get_mainboard_cards()
    total_mainboard = sum(dc.quantity for dc in mainboard if not dc.is_commander)
    
    print(f"\n📦 Deck Size:")
    print(f"   Mainboard: {total_mainboard}")
    print(f"   Commander: 1")
    print(f"   Total: {total_mainboard + 1}")
    
    return deck


def test_commander_singleton_enforcement():
    """Test that singleton rule is properly enforced in Commander decks."""
    print("\n" + "="*60)
    print("TEST: Commander Singleton Enforcement")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    deck = generator.generate_deck(
        archetype='aggro',
        format='commander',
        colors=['R'],
        auto_select_commander=True
    )
    
    print(f"\n🔍 Checking Singleton Rule...")
    
    mainboard = deck.get_mainboard_cards()
    violations = []
    basic_lands = []
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line
        
        if is_basic:
            basic_lands.append(f"{dc.card.name}: {dc.quantity} copies")
        elif dc.quantity > 1:
            violations.append(f"{dc.card.name}: {dc.quantity} copies (should be 1)")
    
    print(f"\n📊 Results:")
    print(f"   Total unique cards: {len(mainboard)}")
    print(f"   Singleton violations: {len(violations)}")
    print(f"   Basic lands with multiple copies: {len(basic_lands)}")
    
    if violations:
        print(f"\n   ❌ Singleton Violations:")
        for v in violations[:10]:
            print(f"      {v}")
        assert False, f"Found {len(violations)} singleton violations"
    else:
        print(f"   ✅ All non-basic cards are singleton")
    
    if basic_lands:
        print(f"\n   ℹ️ Basic Lands (allowed multiple copies):")
        for bl in basic_lands[:5]:
            print(f"      {bl}")
    
    return deck


def test_commander_color_identity():
    """Test that all cards match commander's color identity."""
    print("\n" + "="*60)
    print("TEST: Commander Color Identity Validation")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Boros (R/W) Commander deck
    deck = generator.generate_deck(
        archetype='aggro',
        format='commander',
        colors=['R', 'W'],
        auto_select_commander=True
    )
    
    commander_dc = deck.get_commander()
    
    if not commander_dc:
        print("   ⚠️ No commander found, cannot validate color identity")
        return None
    
    commander_colors = set(commander_dc.card.get_color_identity_list())
    print(f"\n👑 Commander: {commander_dc.card.name}")
    print(f"   Color Identity: {commander_colors}")
    
    mainboard = deck.get_mainboard_cards()
    violations = []
    
    print(f"\n🎨 Checking Color Identity...")
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_colors = set(dc.card.get_color_identity_list())
        
        # Check if card's colors are subset of commander's colors
        if not card_colors.issubset(commander_colors):
            violations.append({
                'name': dc.card.name,
                'colors': card_colors,
                'commander_colors': commander_colors
            })
    
    print(f"\n📊 Results:")
    print(f"   Total cards checked: {len(mainboard) - 1}")  # Exclude commander
    print(f"   Color violations: {len(violations)}")
    
    if violations:
        print(f"\n   ❌ Color Identity Violations:")
        for v in violations[:10]:
            print(f"      {v['name']}: {v['colors']} (commander: {v['commander_colors']})")
        assert False, f"Found {len(violations)} color identity violations"
    else:
        print(f"   ✅ All cards match commander color identity")
    
    return deck


def test_commander_deck_size():
    """Test that Commander decks have exactly 100 cards (99 + commander)."""
    print("\n" + "="*60)
    print("TEST: Commander Deck Size (100 cards)")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    test_cases = [
        {'colors': ['R'], 'archetype': 'aggro'},
        {'colors': ['G'], 'archetype': 'midrange'},
        {'colors': ['U', 'B'], 'archetype': 'control'},
    ]
    
    print(f"\n🧪 Testing {len(test_cases)} configurations...")
    
    all_passed = True
    
    for i, config in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {config['colors']} {config['archetype']}")
        
        deck = generator.generate_deck(
            archetype=config['archetype'],
            format='commander',
            colors=config['colors'],
            auto_select_commander=True
        )
        
        commander_dc = deck.get_commander()
        mainboard = deck.get_mainboard_cards()
        
        # Count cards (excluding commander from mainboard count)
        mainboard_count = sum(dc.quantity for dc in mainboard if not dc.is_commander)
        commander_count = 1 if commander_dc else 0
        total = mainboard_count + commander_count
        
        print(f"      Mainboard: {mainboard_count}")
        print(f"      Commander: {commander_count}")
        print(f"      Total: {total}")
        
        if total == 100:
            print(f"      ✅ Correct size")
        else:
            print(f"      ❌ Wrong size (expected 100, got {total})")
            all_passed = False
    
    if all_passed:
        print(f"\n✅ All deck size tests passed")
    else:
        print(f"\n❌ Some deck size tests failed")
        assert False, "Deck size validation failed"
    
    return True


def test_commander_no_suitable_commander():
    """Test behavior when no suitable commander exists in collection."""
    print("\n" + "="*60)
    print("TEST: No Suitable Commander Available")
    print("="*60)
    
    # Create collection with no legendary creatures
    collection = [
        Card(
            name="Lightning Bolt",
            set_code="M10",
            collector_number="146",
            type_line="Instant",
            card_types="Instant",
            mana_cost="{R}",
            cmc=1.0,
            colors="R",
            color_identity="R",
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            scryfall_id=f"bolt-{i}"
        )
        for i in range(100)
    ]
    
    # Add basic lands
    for i in range(50):
        collection.append(Card(
            name="Mountain",
            set_code="M10",
            collector_number="245",
            type_line="Basic Land - Mountain",
            card_types="Land",
            colors="",
            color_identity="R",
            oracle_text="{T}: Add {R}.",
            scryfall_id=f"mountain-{i}"
        ))
    
    generator = DeckGenerator(collection)
    
    print(f"\n⚠️ Generating Commander deck with no legendary creatures...")
    
    try:
        deck = generator.generate_deck(
            archetype='aggro',
            format='commander',
            colors=['R'],
            auto_select_commander=True
        )
        
        commander_dc = deck.get_commander()
        
        if commander_dc:
            print(f"   ❌ Unexpectedly found commander: {commander_dc.card.name}")
            assert False, "Should not have found a commander"
        else:
            print(f"   ✅ No commander selected (as expected)")
            print(f"   ✅ Deck generated successfully without commander")
        
        return deck
        
    except Exception as e:
        print(f"   ⚠️ Exception raised: {e}")
        print(f"   ℹ️ This is acceptable behavior")
        return None


def test_compare_standard_vs_commander():
    """Compare Standard vs Commander deck generation for same archetype."""
    print("\n" + "="*60)
    print("TEST: Compare Standard vs Commander Generation")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Standard deck
    print(f"\n🎴 Generating Standard deck...")
    standard_deck = generator.generate_deck(
        archetype='midrange',
        format='standard',
        colors=['R', 'G'],
        deck_size=60
    )
    
    # Generate Commander deck
    print(f"\n👑 Generating Commander deck...")
    commander_deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=['R', 'G'],
        auto_select_commander=True
    )
    
    # Analyze both
    std_analyzer = DeckAnalyzer(standard_deck)
    cmd_analyzer = DeckAnalyzer(commander_deck)
    
    std_analysis = std_analyzer.analyze_deck()
    cmd_analysis = cmd_analyzer.analyze_deck()
    
    std_mainboard = standard_deck.get_mainboard_cards()
    cmd_mainboard = commander_deck.get_mainboard_cards()
    
    std_total = sum(dc.quantity for dc in std_mainboard)
    cmd_total = sum(dc.quantity for dc in cmd_mainboard if not dc.is_commander)
    
    # Print comparison
    print("\n" + "="*60)
    print("COMPARISON: STANDARD vs COMMANDER")
    print("="*60)
    
    print(f"\n{'Metric':<25} {'Standard':<15} {'Commander':<15}")
    print("-" * 60)
    print(f"{'Format':<25} {standard_deck.format:<15} {commander_deck.format:<15}")
    print(f"{'Total Cards':<25} {std_total:<15} {cmd_total + 1:<15}")  # +1 for commander
    print(f"{'Unique Cards':<25} {len(std_mainboard):<15} {len(cmd_mainboard):<15}")
    print(f"{'Creatures':<25} {std_analysis['card_types'].get('creature', 0):<15} {cmd_analysis['card_types'].get('creature', 0):<15}")
    print(f"{'Removal Spells':<25} {std_analysis['removal_count']:<15} {cmd_analysis['removal_count']:<15}")
    print(f"{'Ramp':<25} {std_analysis['ramp_count']:<15} {cmd_analysis['ramp_count']:<15}")
    print(f"{'Card Draw':<25} {std_analysis['card_draw_count']:<15} {cmd_analysis['card_draw_count']:<15}")
    
    # Check for commander
    commander_dc = commander_deck.get_commander()
    if commander_dc:
        print(f"\n👑 Commander: {commander_dc.card.name}")
    else:
        print(f"\n⚠️ No commander found in Commander deck")
    
    # Calculate average CMC
    std_curve = std_analysis['mana_curve']
    cmd_curve = cmd_analysis['mana_curve']
    
    std_total_nonland = sum(std_curve.values())
    cmd_total_nonland = sum(cmd_curve.values())
    
    std_avg_cmc = sum(cmc * count for cmc, count in std_curve.items()) / std_total_nonland if std_total_nonland > 0 else 0
    cmd_avg_cmc = sum(cmc * count for cmc, count in cmd_curve.items()) / cmd_total_nonland if cmd_total_nonland > 0 else 0
    
    print(f"{'Average CMC':<25} {std_avg_cmc:<15.2f} {cmd_avg_cmc:<15.2f}")
    
    print("\n✅ Comparison complete")
    
    return {
        'standard': standard_deck,
        'commander': commander_deck
    }

def main():
    print("\n" + "🧬" * 30)
    print("AI DECK GENERATOR TEST SUITE")
    print("🧬" * 30)
    
    try:
        # Original tests
        print("\n" + "📦" * 30)
        print("STANDARD FORMAT TESTS")
        print("📦" * 30)
        
        aggro_deck = test_generate_aggro_deck()
        control_deck = test_generate_control_deck()
        midrange_deck = test_generate_midrange_deck()
        comparison = test_compare_archetypes()
        
        # Commander tests
        print("\n\n" + "👑" * 30)
        print("COMMANDER FORMAT TESTS")
        print("👑" * 30)
        
        cmd_auto = test_generate_commander_deck_with_auto_selection()
        cmd_manual = test_generate_commander_deck_with_manual_commander()
        cmd_singleton = test_commander_singleton_enforcement()
        cmd_colors = test_commander_color_identity()
        cmd_size = test_commander_deck_size()
        cmd_no_commander = test_commander_no_suitable_commander()
        cmd_comparison = test_compare_standard_vs_commander()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   Standard Format Tests: 4")
        print(f"   Commander Format Tests: 7")
        print(f"   Total Tests: 11")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

def test_generate_commander_deck_with_auto_selection():
    """Test Commander deck generation with automatic commander selection."""
    print("\n" + "="*60)
    print("TEST: Generate Commander Deck (Auto-Select Commander)")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Gruul (R/G) Commander deck with auto-selection
    deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=['R', 'G'],
        deck_size=99,  # Will be adjusted automatically
        commander=None,  # Let it auto-select
        auto_select_commander=True
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    print(f"   Format: {deck.format}")
    
    # Get commander
    commander_dc = deck.get_commander()
    
    # Validate commander
    print(f"\n👑 Commander Validation:")
    if commander_dc:
        print(f"   ✅ Commander: {commander_dc.card.name}")
        print(f"   Type: {commander_dc.card.type_line}")
        print(f"   Colors: {commander_dc.card.color_identity}")
        
        # Check if legendary creature
        assert 'Legendary' in commander_dc.card.type_line, "Commander must be legendary"
        assert 'Creature' in commander_dc.card.type_line, "Commander must be a creature"
        print(f"   ✅ Is Legendary Creature: True")
        
        # Check quantity
        assert commander_dc.quantity == 1, "Commander must have quantity of 1"
        print(f"   ✅ Quantity: {commander_dc.quantity}")
    else:
        print(f"   ⚠️ No commander found!")
    
    # Validate deck size
    mainboard = deck.get_mainboard_cards()
    total_mainboard = sum(dc.quantity for dc in mainboard if not dc.is_commander)
    
    print(f"\n📦 Deck Size Validation:")
    print(f"   Mainboard (excluding commander): {total_mainboard}")
    print(f"   Commander: {1 if commander_dc else 0}")
    print(f"   Total: {total_mainboard + (1 if commander_dc else 0)}")
    
    expected_total = 100
    actual_total = total_mainboard + (1 if commander_dc else 0)
    if actual_total == expected_total:
        print(f"   ✅ Deck size is correct: {actual_total}/100")
    else:
        print(f"   ⚠️ Deck size mismatch: {actual_total}/100")
    
    # Validate singleton rule (except basic lands)
    print(f"\n🎯 Singleton Rule Validation:")
    card_counts = {}
    violations = []
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_name = dc.card.name
        is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line
        
        if card_name not in card_counts:
            card_counts[card_name] = 0
        card_counts[card_name] += dc.quantity
        
        # Check singleton (except basic lands)
        if not is_basic and dc.quantity > 1:
            violations.append(f"{card_name}: {dc.quantity} copies")
    
    if violations:
        print(f"   ❌ Singleton violations found:")
        for v in violations:
            print(f"      {v}")
    else:
        print(f"   ✅ All non-basic cards are singleton")
    
    # Validate color identity
    print(f"\n🎨 Color Identity Validation:")
    commander_colors = set(commander_dc.card.get_color_identity_list()) if commander_dc else set()
    print(f"   Commander color identity: {commander_colors}")
    
    color_violations = []
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_colors = set(dc.card.get_color_identity_list())
        if not card_colors.issubset(commander_colors):
            color_violations.append(f"{dc.card.name}: {card_colors} (not in {commander_colors})")
    
    if color_violations:
        print(f"   ❌ Color identity violations:")
        for v in color_violations[:5]:  # Show first 5
            print(f"      {v}")
    else:
        print(f"   ✅ All cards match commander color identity")
    
    # Analyze deck
    analyzer = DeckAnalyzer(deck)
    analysis = analyzer.analyze_deck()
    
    print(f"\n📊 Deck Analysis:")
    print(f"   Colors: {analysis['colors']}")
    print(f"   Creatures: {analysis['card_types'].get('creature', 0)}")
    print(f"   Removal: {analysis['removal_count']}")
    print(f"   Ramp: {analysis['ramp_count']}")
    print(f"   Card Draw: {analysis['card_draw_count']}")
    
    print(f"\n📈 Mana Curve:")
    for cmc in sorted(analysis['mana_curve'].keys()):
        count = analysis['mana_curve'][cmc]
        bar = '█' * min(count, 50)  # Cap display at 50
        print(f"   CMC {cmc}: {bar} ({count})")
    
    print(f"\n🎯 Top Themes:")
    for theme, count in sorted(analysis['themes'].items(), key=lambda x: -x[1])[:5]:
        print(f"   {theme}: {count}")
    
    print(f"\n📋 Sample Cards (first 20):")
    for dc in mainboard[:20]:
        if dc.is_commander:
            print(f"   👑 {dc.quantity}x {dc.card.name} (COMMANDER)")
        else:
            print(f"   {dc.quantity}x {dc.card.name} ({dc.card.mana_cost or 'Land'})")
    
    return deck


def test_generate_commander_deck_with_manual_commander():
    """Test Commander deck generation with manually specified commander."""
    print("\n" + "="*60)
    print("TEST: Generate Commander Deck (Manual Commander)")
    print("="*60)
    
    collection = create_test_collection()
    
    # Find a suitable commander from collection
    suitable_commanders = [
        c for c in collection
        if c.type_line and 'Legendary Creature' in c.type_line
    ]
    
    if not suitable_commanders:
        print("   ⚠️ No legendary creatures in test collection, skipping test")
        return None
    
    # Pick first suitable commander
    chosen_commander = suitable_commanders[0]
    commander_colors = chosen_commander.get_color_identity_list()
    
    print(f"\n👑 Chosen Commander:")
    print(f"   Name: {chosen_commander.name}")
    print(f"   Type: {chosen_commander.type_line}")
    print(f"   Colors: {commander_colors}")
    print(f"   CMC: {chosen_commander.cmc}")
    
    generator = DeckGenerator(collection)
    
    # Generate deck with specified commander
    deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=commander_colors,
        commander=chosen_commander,
        auto_select_commander=False
    )
    
    print(f"\n✅ Generated deck: {deck.name}")
    
    # Validate commander matches
    commander_dc = deck.get_commander()
    
    print(f"\n🔍 Commander Verification:")
    if commander_dc:
        matches = commander_dc.card.name == chosen_commander.name
        print(f"   Commander in deck: {commander_dc.card.name}")
        print(f"   Expected: {chosen_commander.name}")
        print(f"   ✅ Match: {matches}")
        
        assert matches, f"Commander mismatch: expected {chosen_commander.name}, got {commander_dc.card.name}"
    else:
        print(f"   ❌ No commander found in deck!")
        assert False, "Commander not found in generated deck"
    
    # Validate deck
    mainboard = deck.get_mainboard_cards()
    total_mainboard = sum(dc.quantity for dc in mainboard if not dc.is_commander)
    
    print(f"\n📦 Deck Size:")
    print(f"   Mainboard: {total_mainboard}")
    print(f"   Commander: 1")
    print(f"   Total: {total_mainboard + 1}")
    
    return deck


def test_commander_singleton_enforcement():
    """Test that singleton rule is properly enforced in Commander decks."""
    print("\n" + "="*60)
    print("TEST: Commander Singleton Enforcement")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    deck = generator.generate_deck(
        archetype='aggro',
        format='commander',
        colors=['R'],
        auto_select_commander=True
    )
    
    print(f"\n🔍 Checking Singleton Rule...")
    
    mainboard = deck.get_mainboard_cards()
    violations = []
    basic_lands = []
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        is_basic = dc.card.type_line and 'Basic Land' in dc.card.type_line
        
        if is_basic:
            basic_lands.append(f"{dc.card.name}: {dc.quantity} copies")
        elif dc.quantity > 1:
            violations.append(f"{dc.card.name}: {dc.quantity} copies (should be 1)")
    
    print(f"\n📊 Results:")
    print(f"   Total unique cards: {len(mainboard)}")
    print(f"   Singleton violations: {len(violations)}")
    print(f"   Basic lands with multiple copies: {len(basic_lands)}")
    
    if violations:
        print(f"\n   ❌ Singleton Violations:")
        for v in violations[:10]:
            print(f"      {v}")
        assert False, f"Found {len(violations)} singleton violations"
    else:
        print(f"   ✅ All non-basic cards are singleton")
    
    if basic_lands:
        print(f"\n   ℹ️ Basic Lands (allowed multiple copies):")
        for bl in basic_lands[:5]:
            print(f"      {bl}")
    
    return deck


def test_commander_color_identity():
    """Test that all cards match commander's color identity."""
    print("\n" + "="*60)
    print("TEST: Commander Color Identity Validation")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Boros (R/W) Commander deck
    deck = generator.generate_deck(
        archetype='aggro',
        format='commander',
        colors=['R', 'W'],
        auto_select_commander=True
    )
    
    commander_dc = deck.get_commander()
    
    if not commander_dc:
        print("   ⚠️ No commander found, cannot validate color identity")
        return None
    
    commander_colors = set(commander_dc.card.get_color_identity_list())
    print(f"\n👑 Commander: {commander_dc.card.name}")
    print(f"   Color Identity: {commander_colors}")
    
    mainboard = deck.get_mainboard_cards()
    violations = []
    
    print(f"\n🎨 Checking Color Identity...")
    
    for dc in mainboard:
        if dc.is_commander:
            continue
        
        card_colors = set(dc.card.get_color_identity_list())
        
        # Check if card's colors are subset of commander's colors
        if not card_colors.issubset(commander_colors):
            violations.append({
                'name': dc.card.name,
                'colors': card_colors,
                'commander_colors': commander_colors
            })
    
    print(f"\n📊 Results:")
    print(f"   Total cards checked: {len(mainboard) - 1}")  # Exclude commander
    print(f"   Color violations: {len(violations)}")
    
    if violations:
        print(f"\n   ❌ Color Identity Violations:")
        for v in violations[:10]:
            print(f"      {v['name']}: {v['colors']} (commander: {v['commander_colors']})")
        assert False, f"Found {len(violations)} color identity violations"
    else:
        print(f"   ✅ All cards match commander color identity")
    
    return deck


def test_commander_deck_size():
    """Test that Commander decks have exactly 100 cards (99 + commander)."""
    print("\n" + "="*60)
    print("TEST: Commander Deck Size (100 cards)")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    test_cases = [
        {'colors': ['R'], 'archetype': 'aggro'},
        {'colors': ['G'], 'archetype': 'midrange'},
        {'colors': ['U', 'B'], 'archetype': 'control'},
    ]
    
    print(f"\n🧪 Testing {len(test_cases)} configurations...")
    
    all_passed = True
    
    for i, config in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {config['colors']} {config['archetype']}")
        
        deck = generator.generate_deck(
            archetype=config['archetype'],
            format='commander',
            colors=config['colors'],
            auto_select_commander=True
        )
        
        commander_dc = deck.get_commander()
        mainboard = deck.get_mainboard_cards()
        
        # Count cards (excluding commander from mainboard count)
        mainboard_count = sum(dc.quantity for dc in mainboard if not dc.is_commander)
        commander_count = 1 if commander_dc else 0
        total = mainboard_count + commander_count
        
        print(f"      Mainboard: {mainboard_count}")
        print(f"      Commander: {commander_count}")
        print(f"      Total: {total}")
        
        if total == 100:
            print(f"      ✅ Correct size")
        else:
            print(f"      ❌ Wrong size (expected 100, got {total})")
            all_passed = False
    
    if all_passed:
        print(f"\n✅ All deck size tests passed")
    else:
        print(f"\n❌ Some deck size tests failed")
        assert False, "Deck size validation failed"
    
    return True


def test_commander_no_suitable_commander():
    """Test behavior when no suitable commander exists in collection."""
    print("\n" + "="*60)
    print("TEST: No Suitable Commander Available")
    print("="*60)
    
    # Create collection with no legendary creatures
    collection = [
        Card(
            name="Lightning Bolt",
            set_code="M10",
            collector_number="146",
            type_line="Instant",
            card_types="Instant",
            mana_cost="{R}",
            cmc=1.0,
            colors="R",
            color_identity="R",
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            scryfall_id=f"bolt-{i}"
        )
        for i in range(100)
    ]
    
    # Add basic lands
    for i in range(50):
        collection.append(Card(
            name="Mountain",
            set_code="M10",
            collector_number="245",
            type_line="Basic Land - Mountain",
            card_types="Land",
            colors="",
            color_identity="R",
            oracle_text="{T}: Add {R}.",
            scryfall_id=f"mountain-{i}"
        ))
    
    generator = DeckGenerator(collection)
    
    print(f"\n⚠️ Generating Commander deck with no legendary creatures...")
    
    try:
        deck = generator.generate_deck(
            archetype='aggro',
            format='commander',
            colors=['R'],
            auto_select_commander=True
        )
        
        commander_dc = deck.get_commander()
        
        if commander_dc:
            print(f"   ❌ Unexpectedly found commander: {commander_dc.card.name}")
            assert False, "Should not have found a commander"
        else:
            print(f"   ✅ No commander selected (as expected)")
            print(f"   ✅ Deck generated successfully without commander")
        
        return deck
        
    except Exception as e:
        print(f"   ⚠️ Exception raised: {e}")
        print(f"   ℹ️ This is acceptable behavior")
        return None


def test_compare_standard_vs_commander():
    """Compare Standard vs Commander deck generation for same archetype."""
    print("\n" + "="*60)
    print("TEST: Compare Standard vs Commander Generation")
    print("="*60)
    
    collection = create_test_collection()
    generator = DeckGenerator(collection)
    
    # Generate Standard deck
    print(f"\n🎴 Generating Standard deck...")
    standard_deck = generator.generate_deck(
        archetype='midrange',
        format='standard',
        colors=['R', 'G'],
        deck_size=60
    )
    
    # Generate Commander deck
    print(f"\n👑 Generating Commander deck...")
    commander_deck = generator.generate_deck(
        archetype='midrange',
        format='commander',
        colors=['R', 'G'],
        auto_select_commander=True
    )
    
    # Analyze both
    std_analyzer = DeckAnalyzer(standard_deck)
    cmd_analyzer = DeckAnalyzer(commander_deck)
    
    std_analysis = std_analyzer.analyze_deck()
    cmd_analysis = cmd_analyzer.analyze_deck()
    
    std_mainboard = standard_deck.get_mainboard_cards()
    cmd_mainboard = commander_deck.get_mainboard_cards()
    
    std_total = sum(dc.quantity for dc in std_mainboard)
    cmd_total = sum(dc.quantity for dc in cmd_mainboard if not dc.is_commander)
    
    # Print comparison
    print("\n" + "="*60)
    print("COMPARISON: STANDARD vs COMMANDER")
    print("="*60)
    
    print(f"\n{'Metric':<25} {'Standard':<15} {'Commander':<15}")
    print("-" * 60)
    print(f"{'Format':<25} {standard_deck.format:<15} {commander_deck.format:<15}")
    print(f"{'Total Cards':<25} {std_total:<15} {cmd_total + 1:<15}")  # +1 for commander
    print(f"{'Unique Cards':<25} {len(std_mainboard):<15} {len(cmd_mainboard):<15}")
    print(f"{'Creatures':<25} {std_analysis['card_types'].get('creature', 0):<15} {cmd_analysis['card_types'].get('creature', 0):<15}")
    print(f"{'Removal Spells':<25} {std_analysis['removal_count']:<15} {cmd_analysis['removal_count']:<15}")
    print(f"{'Ramp':<25} {std_analysis['ramp_count']:<15} {cmd_analysis['ramp_count']:<15}")
    print(f"{'Card Draw':<25} {std_analysis['card_draw_count']:<15} {cmd_analysis['card_draw_count']:<15}")
    
    # Check for commander
    commander_dc = commander_deck.get_commander()
    if commander_dc:
        print(f"\n👑 Commander: {commander_dc.card.name}")
    else:
        print(f"\n⚠️ No commander found in Commander deck")
    
    # Calculate average CMC
    std_curve = std_analysis['mana_curve']
    cmd_curve = cmd_analysis['mana_curve']
    
    std_total_nonland = sum(std_curve.values())
    cmd_total_nonland = sum(cmd_curve.values())
    
    std_avg_cmc = sum(cmc * count for cmc, count in std_curve.items()) / std_total_nonland if std_total_nonland > 0 else 0
    cmd_avg_cmc = sum(cmc * count for cmc, count in cmd_curve.items()) / cmd_total_nonland if cmd_total_nonland > 0 else 0
    
    print(f"{'Average CMC':<25} {std_avg_cmc:<15.2f} {cmd_avg_cmc:<15.2f}")
    
    print("\n✅ Comparison complete")
    
    return {
        'standard': standard_deck,
        'commander': commander_deck
    }