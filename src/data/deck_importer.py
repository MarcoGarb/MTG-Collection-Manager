# -*- coding: utf-8 -*-
""" Deck importer for Manabox exports (CSV and TXT formats). """

import csv
import re
from typing import List, Tuple, Optional
from pathlib import Path

from src.models.card import Card
from src.models.deck import Deck, DeckCard
from src.data.database import DatabaseManager

class DeckImporter:
    """Import decks from Manabox CSV and TXT formats."""

    BASIC_LANDS = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes']
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.collection_cache = None
        self.missing_cards = []
        self.warnings = []
    
    def import_deck(self, file_path: str, deck_name: Optional[str] = None, 
                   deck_format: str = "standard") -> Tuple[Deck, List[str]]:
        """
        Import a deck from file.
        
        Args:
            file_path: Path to the deck file (.txt or .csv)
            deck_name: Name for the deck (defaults to filename)
            deck_format: Format for the deck
            
        Returns:
            Tuple of (Deck object, list of warnings)
        """
        self.missing_cards = []
        self.warnings = []
        
        # Load collection once
        if self.collection_cache is None:
            self.collection_cache = self.db.get_all_cards()
        
        # Determine file type and parse
        file_path = Path(file_path)
        
        if not deck_name:
            deck_name = file_path.stem
        
        if file_path.suffix.lower() == '.txt':
            card_list = self._parse_txt(file_path)
        elif file_path.suffix.lower() == '.csv':
            card_list = self._parse_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Create deck
        deck = Deck(name=deck_name, format=deck_format)
        
        # Match cards to collection
        for quantity, card_name, set_code, collector_number, is_sideboard in card_list:
            card = self._find_card_in_collection(card_name, set_code, collector_number)
            
            if card:
                deck.add_card(card, quantity=quantity, in_sideboard=is_sideboard)
            else:
                # Check if it's a basic land
                if card_name in self.BASIC_LANDS:
                    basic_land = self._create_basic_land(card_name)
                    deck.add_card(basic_land, quantity=quantity, in_sideboard=is_sideboard)
                else:
                    self.missing_cards.append(f"{quantity}x {card_name} ({set_code}) {collector_number}")
                    self.warnings.append(f"Card not in collection: {card_name} ({set_code}) #{collector_number}")
        
        deck.update_colors()
        
        return deck, self.warnings
    
    def _parse_txt(self, file_path: Path) -> List[Tuple[int, str, str, str, bool]]:
        """
        Parse Manabox TXT format.
        Format: Quantity CardName (SetCode) CollectorNumber
        Example: 1 Boneknitter (ONS) 128
        
        Returns list of (quantity, name, set_code, collector_number, is_sideboard)
        """
        card_list = []
        is_sideboard = False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Check for sideboard marker
                if line.lower() in ['sideboard', '// sideboard', 'sideboard:']:
                    is_sideboard = True
                    continue
                
                if not line or line.startswith('//'):
                    continue
                
                # Parse line: "1 Boneknitter (ONS) 128"
                match = re.match(r'^(\d+)\s+(.+?)\s+\(([A-Z0-9]+)\)\s+(\S+)$', line)
                
                if match:
                    quantity = int(match.group(1))
                    card_name = match.group(2).strip()
                    set_code = match.group(3).upper()
                    collector_number = match.group(4)
                    
                    card_list.append((quantity, card_name, set_code, collector_number, is_sideboard))
                else:
                    self.warnings.append(f"Could not parse line: {line}")
        
        return card_list
    
    def _parse_csv(self, file_path: Path) -> List[Tuple[int, str, str, str, bool]]:
        """
        Parse Manabox CSV format.
        Headers: Name, Set code, Collector number, Quantity, etc.
        
        Returns list of (quantity, name, set_code, collector_number, is_sideboard)
        """
        card_list = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Manabox CSV is tab-separated
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                try:
                    quantity = int(row['Quantity'])
                    card_name = row['Name'].strip()
                    set_code = row['Set code'].upper()
                    collector_number = row['Collector number'].strip()
                    
                    # CSV doesn't have sideboard marker, all mainboard
                    card_list.append((quantity, card_name, set_code, collector_number, False))
                
                except (KeyError, ValueError) as e:
                    self.warnings.append(f"Error parsing row: {e}")
                    continue
        
        return card_list
    
    def _find_card_in_collection(self, name: str, set_code: str, 
                                collector_number: str) -> Optional[Card]:
        """Find a card in the collection by name, set, and collector number."""
        # First try exact match (name + set + collector number)
        for card in self.collection_cache:
            if (card.name.lower() == name.lower() and 
                card.set_code.upper() == set_code.upper() and
                card.collector_number == collector_number):
                return card
        
        # Try match by name and set only
        for card in self.collection_cache:
            if (card.name.lower() == name.lower() and 
                card.set_code.upper() == set_code.upper()):
                return card
        
        # Try match by name only (any printing)
        for card in self.collection_cache:
            if card.name.lower() == name.lower():
                self.warnings.append(
                    f"Using different printing for {name}: "
                    f"Found {card.set_code.upper()} instead of {set_code}"
                )
                return card
        
        return None
    
    def _create_basic_land(self, land_name: str) -> Card:
        """Create a virtual basic land card."""
        land_data = {
            'Plains': {'colors': 'W', 'type': 'Basic Land - Plains', 'text': '({T}: Add {W}.)'},
            'Island': {'colors': 'U', 'type': 'Basic Land - Island', 'text': '({T}: Add {U}.)'},
            'Swamp': {'colors': 'B', 'type': 'Basic Land - Swamp', 'text': '({T}: Add {B}.)'},
            'Mountain': {'colors': 'R', 'type': 'Basic Land - Mountain', 'text': '({T}: Add {R}.)'},
            'Forest': {'colors': 'G', 'type': 'Basic Land - Forest', 'text': '({T}: Add {G}.)'},
            'Wastes': {'colors': '', 'type': 'Basic Land - Wastes', 'text': '({T}: Add {C}.)'},
        }
    
        info = land_data.get(land_name, land_data['Plains'])
    
        return Card(
            name=land_name,
            set_code='BASIC',
            collector_number='0',
            rarity='common',
            mana_cost='',
            cmc=0.0,
            colors=info['colors'],
            color_identity=info['colors'],
            type_line=info['type'],
            card_types='Land,Basic',
            subtypes=land_name,
            oracle_text=info['text'],
            quantity=999,
            id=-ord(land_name[0])
        )