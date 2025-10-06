"""
Import cards from Manabox CSV export.
"""
import pandas as pd
from pathlib import Path
from typing import List
from src.models.card import Card


"""
Import cards from Manabox CSV export.
"""
import pandas as pd
from pathlib import Path
from typing import List
from src.models.card import Card


class CSVImporter:
    """Import cards from CSV files."""
    
    @staticmethod
    def import_from_manabox(csv_path: str) -> List[Card]:
        """
        Import cards from Manabox CSV export.
        Returns a list of Card objects.
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"Loading CSV from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows")
        
        # Display available columns for debugging
        print(f"Columns found: {list(df.columns)}")
        
        cards = []
        
        for idx, row in df.iterrows():
            try:
                # Map CSV columns to Card fields using exact column names from Manabox
                
                # Convert foil - Manabox uses "normal" or "foil" strings
                is_foil = str(row.get('Foil', 'normal')).lower() == 'foil'
                
                # Get collector number
                collector_num = str(row.get('Collector number', ''))
                
                # Get purchase price (Manabox doesn't include market price in export)
                purchase_price = None
                if pd.notna(row.get('Purchase price')):
                    try:
                        purchase_price = float(row.get('Purchase price', 0))
                    except:
                        purchase_price = None
                
                card = Card(
                    name=str(row.get('Name', '')),
                    set_code=str(row.get('Set code', '')),
                    collector_number=collector_num,
                    rarity=str(row.get('Rarity', '')) if pd.notna(row.get('Rarity')) else None,
                    language=str(row.get('Language', 'en')),
                    foil=is_foil,
                    condition=str(row.get('Condition', '')) if pd.notna(row.get('Condition')) else None,
                    purchase_price=purchase_price,
                    current_price=None,  # Manabox CSV doesn't include current market price
                    scryfall_id=None,  # Not in Manabox export - we'll fetch this via API later
                    quantity=int(row.get('Quantity', 1))
                )
                cards.append(card)
                
            except Exception as e:
                print(f"Warning: Skipped row {idx} due to error: {e}")
                continue
        
        print(f"✓ Parsed {len(cards)} cards successfully")
        return cards
    
    @staticmethod
    def detect_columns(csv_path: str) -> List[str]:
        """Return list of column names from CSV."""
        df = pd.read_csv(csv_path, nrows=0)
        return list(df.columns)