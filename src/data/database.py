# src/data/database.py
""" Database operations for the MTG collection. """
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.card import Card
from src.models.deck import Deck, DeckCard


class DatabaseManager:
    """Manages SQLite database operations for the collection."""

    def __init__(self, db_path: str = "data/collection.db"):
        """Initialize database connection (lazy connect)."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self):
        """Establish database connection."""
        if self.connection:
            return
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.connection.cursor()
        # Enforce foreign keys for deck tables
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def initialize_schema(self):
        """Create the database schema if it doesn't exist."""
        assert self.cursor is not None, "Call connect() before initialize_schema()"

        # Cards table (includes gameplay fields)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                set_code TEXT NOT NULL,
                collector_number TEXT NOT NULL,
                rarity TEXT,
                language TEXT DEFAULT 'en',
                foil INTEGER DEFAULT 0,
                condition TEXT,
                purchase_price REAL,
                current_price REAL,
                scryfall_id TEXT,
                oracle_id TEXT,
                quantity INTEGER DEFAULT 1,
                tags TEXT,
                notes TEXT,
                date_added TEXT,

                -- Gameplay fields
                mana_cost TEXT,
                cmc REAL,
                colors TEXT,
                color_identity TEXT,
                type_line TEXT,
                card_types TEXT,
                subtypes TEXT,
                oracle_text TEXT,

                UNIQUE(name, set_code, collector_number, foil, condition)
            )
        """)

        # Decks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                format TEXT NOT NULL,
                description TEXT,
                colors TEXT,
                date_created TEXT,
                date_modified TEXT
            )
        """)

        # Deck cards pivot
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS deck_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                is_commander INTEGER DEFAULT 0,
                in_sideboard INTEGER DEFAULT 0,
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(id)
            )
        """)

        self.connection.commit()

    # -------------------------
    # Cards: CRUD and queries
    # -------------------------
    def add_card(self, card: Card) -> int:
        """
        Add a card to the collection or update quantity if it exists.
        Returns the card ID.
        """
        assert self.cursor is not None, "Database not connected"

        if card.date_added is None:
            card.date_added = datetime.now().isoformat()

        # Check if card already exists (match condition even if NULL)
        self.cursor.execute("""
            SELECT id, quantity FROM cards 
            WHERE name = ? AND set_code = ? AND collector_number = ? 
              AND foil = ? AND COALESCE(condition, '') = COALESCE(?, '')
        """, (card.name, card.set_code, card.collector_number,
              1 if card.foil else 0, card.condition))
        existing = self.cursor.fetchone()

        if existing:
            new_quantity = (existing["quantity"] or 0) + (card.quantity or 1)
            self.cursor.execute("""
                UPDATE cards SET quantity = ? WHERE id = ?
            """, (new_quantity, existing["id"]))
            self.connection.commit()
            return existing["id"]
        else:
            self.cursor.execute("""
                INSERT INTO cards (
                    name, set_code, collector_number, rarity, language, foil,
                    condition, purchase_price, current_price, scryfall_id, oracle_id,
                    quantity, tags, notes, date_added,
                    mana_cost, cmc, colors, color_identity, type_line,
                    card_types, subtypes, oracle_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card.name, card.set_code, card.collector_number, card.rarity,
                card.language, 1 if card.foil else 0, card.condition,
                card.purchase_price, card.current_price, card.scryfall_id,
                card.oracle_id, card.quantity, card.tags, card.notes,
                card.date_added,
                card.mana_cost, card.cmc, card.colors, card.color_identity,
                card.type_line, card.card_types, card.subtypes, card.oracle_text
            ))
            self.connection.commit()
            return self.cursor.lastrowid

    def _row_to_card(self, row: sqlite3.Row) -> Card:
        """Convert database row to Card object."""
        def safe_get(key: str):
            try:
                return row[key]
            except (KeyError, IndexError, TypeError):
                return None

        return Card(
            id=row['id'],
            name=row['name'],
            set_code=row['set_code'],
            collector_number=row['collector_number'],
            rarity=row['rarity'],
            language=row['language'],
            foil=bool(row['foil']),
            condition=row['condition'],
            purchase_price=row['purchase_price'],
            current_price=row['current_price'],
            scryfall_id=row['scryfall_id'],
            oracle_id=row['oracle_id'],
            quantity=row['quantity'],
            tags=row['tags'],
            notes=row['notes'],
            date_added=row['date_added'],
            mana_cost=safe_get('mana_cost'),
            cmc=safe_get('cmc'),
            colors=safe_get('colors'),
            color_identity=safe_get('color_identity'),
            type_line=safe_get('type_line'),
            card_types=safe_get('card_types'),
            subtypes=safe_get('subtypes'),
            oracle_text=safe_get('oracle_text'),
        )

    def get_all_cards(self) -> List[Card]:
        """Retrieve all cards from the collection."""
        assert self.cursor is not None
        self.cursor.execute("SELECT * FROM cards ORDER BY name")
        rows = self.cursor.fetchall()
        return [self._row_to_card(row) for row in rows]

    def search_cards(self, query: str) -> List[Card]:
        """Search for cards by name (LIKE)."""
        assert self.cursor is not None
        self.cursor.execute("""
            SELECT * FROM cards 
            WHERE name LIKE ? 
            ORDER BY name
        """, (f"%{query}%",))
        rows = self.cursor.fetchall()
        return [self._row_to_card(row) for row in rows]

    def filter_cards(self, name_query: str = "", filters: Dict[str, Any] = None) -> List[Card]:
        """Search and filter cards by multiple criteria."""
        assert self.cursor is not None
        if filters is None:
            filters = {}

        sql = "SELECT * FROM cards WHERE 1=1"
        params: List[Any] = []

        if name_query:
            sql += " AND name LIKE ?"
            params.append(f"%{name_query}%")

        # Example filters expected by UI FilterPanel (adapt as needed):
        # rarity: 'common' | 'uncommon' | 'rare' | 'mythic'
        if filters.get("rarity"):
            sql += " AND rarity = ?"
            params.append(filters["rarity"].lower())

        # color includes letter(s) W,U,B,R,G
        if filters.get("color"):
            color = filters["color"]
            if color == "Colorless":
                sql += " AND (colors IS NULL OR colors = '' )"
            elif color == "Multicolor":
                sql += " AND colors LIKE '%,%'"
            else:
                sql += " AND (colors LIKE ? OR color_identity LIKE ?)"
                params.extend([f"%{color}%", f"%{color}%"])

        # cmc exact or '7+'
        if filters.get("cmc"):
            cmc_val = filters["cmc"]
            if cmc_val == "7+":
                sql += " AND COALESCE(cmc, 0) >= 7"
            else:
                sql += " AND CAST(COALESCE(cmc, 0) AS INT) = ?"
                params.append(int(cmc_val))

        sql += " ORDER BY name"
        self.cursor.execute(sql, tuple(params))
        rows = self.cursor.fetchall()
        return [self._row_to_card(row) for row in rows]

    def get_collection_stats(self) -> Dict[str, Any]:
        """Aggregate collection statistics."""
        assert self.cursor is not None
        stats: Dict[str, Any] = {}

        self.cursor.execute("SELECT SUM(quantity) FROM cards")
        stats['total_cards'] = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT COUNT(*) FROM cards")
        stats['unique_cards'] = self.cursor.fetchone()[0] or 0

        self.cursor.execute("SELECT SUM(current_price * quantity) FROM cards WHERE current_price IS NOT NULL")
        stats['total_value'] = self.cursor.fetchone()[0] or 0.0

        self.cursor.execute("""
            SELECT rarity, SUM(quantity) as count 
            FROM cards 
            GROUP BY rarity
        """)
        stats['by_rarity'] = {row['rarity']: row['count'] for row in self.cursor.fetchall() if row['rarity']}

        return stats

    def clear_collection(self):
        """Delete all cards from the collection."""
        assert self.cursor is not None
        self.cursor.execute("DELETE FROM cards")
        self.connection.commit()

    # -------------------------
    # Decks: CRUD and queries
    # -------------------------
    def create_deck(self, deck: Deck) -> int:
        """Create a new deck and its cards; returns deck ID."""
        assert self.cursor is not None

        if not deck.date_created:
            deck.date_created = datetime.now().isoformat()
        if not deck.date_modified:
            deck.date_modified = deck.date_created

        # Ensure colors are up to date
        deck.update_colors()

        self.cursor.execute("""
            INSERT INTO decks (name, format, description, colors, date_created, date_modified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (deck.name, deck.format, deck.description, deck.colors, deck.date_created, deck.date_modified))

        deck_id = self.cursor.lastrowid

        for deck_card in deck.cards:
            self.cursor.execute("""
                INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, in_sideboard)
                VALUES (?, ?, ?, ?, ?)
            """, (deck_id, deck_card.card.id, deck_card.quantity,
                  1 if deck_card.is_commander else 0,
                  1 if deck_card.in_sideboard else 0))

        self.connection.commit()
        return deck_id

    def update_deck(self, deck: Deck):
        """Update an existing deck and replace its card list."""
        assert self.cursor is not None
        deck.date_modified = datetime.now().isoformat()
        deck.update_colors()

        self.cursor.execute("""
            UPDATE decks 
            SET name = ?, format = ?, description = ?, colors = ?, date_modified = ?
            WHERE id = ?
        """, (deck.name, deck.format, deck.description, deck.colors, deck.date_modified, deck.id))

        self.cursor.execute("DELETE FROM deck_cards WHERE deck_id = ?", (deck.id,))

        for deck_card in deck.cards:
            self.cursor.execute("""
                INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, in_sideboard)
                VALUES (?, ?, ?, ?, ?)
            """, (deck.id, deck_card.card.id, deck_card.quantity,
                  1 if deck_card.is_commander else 0,
                  1 if deck_card.in_sideboard else 0))

        self.connection.commit()

    def get_deck(self, deck_id: int) -> Optional[Deck]:
        """Load a deck and its cards."""
        assert self.cursor is not None
        self.cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        deck = Deck(
            id=row['id'],
            name=row['name'],
            format=row['format'],
            description=row['description'],
            colors=row['colors'],
            date_created=row['date_created'],
            date_modified=row['date_modified']
        )

        self.cursor.execute("""
            SELECT dc.quantity, dc.is_commander, dc.in_sideboard, c.*
            FROM deck_cards dc
            JOIN cards c ON dc.card_id = c.id
            WHERE dc.deck_id = ?
        """, (deck_id,))

        for r in self.cursor.fetchall():
            card = self._row_to_card(r)
            deck_card = DeckCard(
                card=card,
                quantity=r['quantity'],
                is_commander=bool(r['is_commander']),
                in_sideboard=bool(r['in_sideboard'])
            )
            deck.cards.append(deck_card)

        return deck

    def get_all_decks(self) -> List[Deck]:
        """Return a light list of decks (no full card lists)."""
        assert self.cursor is not None
        self.cursor.execute("SELECT * FROM decks ORDER BY date_modified DESC")
        rows = self.cursor.fetchall()

        decks: List[Deck] = []
        for row in rows:
            deck = Deck(
                id=row['id'],
                name=row['name'],
                format=row['format'],
                description=row['description'],
                colors=row['colors'],
                date_created=row['date_created'],
                date_modified=row['date_modified']
            )
            decks.append(deck)
        return decks

        # NEW
    def get_used_in_decks(self, card_id: int, exclude_deck_id: int | None = None) -> int:
        """
        Sum of copies of this card used by all decks, optionally excluding one deck.
        """
        if exclude_deck_id is None:
            self.cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0) AS used
                FROM deck_cards
                WHERE card_id = ?
            """, (card_id,))
        else:
            self.cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0) AS used
                FROM deck_cards
                WHERE card_id = ? AND deck_id != ?
            """, (card_id, exclude_deck_id))
        row = self.cursor.fetchone()
        return row['used'] if row else 0

    # NEW
    def get_available_quantity_for_deck(self, card_id: int, exclude_deck_id: int | None = None) -> int:
        """
        Maximum copies this deck can still allocate without stealing from others:
        owned - used_in_other_decks.
        """
        self.cursor.execute("SELECT quantity FROM cards WHERE id = ?", (card_id,))
        row = self.cursor.fetchone()
        if not row:
            return 0
        owned = row['quantity'] or 0
        used_elsewhere = self.get_used_in_decks(card_id, exclude_deck_id=exclude_deck_id)
        return max(0, owned - used_elsewhere)

    # NEW
    def get_availability_ledger(self, exclude_deck_id: int | None = None) -> dict[int, int]:
        """
        Dict[card_id] = copies free for THIS deck to take (owned - used_elsewhere).
        """
        if exclude_deck_id is None:
            # used across all decks
            self.cursor.execute("""
                SELECT c.id AS card_id,
                    c.quantity - COALESCE(u.used, 0) AS available
                FROM cards c
                LEFT JOIN (
                    SELECT card_id, SUM(quantity) AS used
                    FROM deck_cards
                    GROUP BY card_id
                ) u ON u.card_id = c.id
            """)
        else:
            # used across all other decks
            self.cursor.execute("""
                SELECT c.id AS card_id,
                    c.quantity - COALESCE(u.used, 0) AS available
                FROM cards c
                LEFT JOIN (
                    SELECT card_id, SUM(quantity) AS used
                    FROM deck_cards
                    WHERE deck_id != ?
                    GROUP BY card_id
                ) u ON u.card_id = c.id
            """, (exclude_deck_id,))
        rows = self.cursor.fetchall()
        return {row['card_id']: max(0, row['available'] or 0) for row in rows}

    # OPTIONAL: tighten this to use the new helpers (kept for specific one-off checks)
    def check_card_availability(self, card_id: int, quantity_needed: int, exclude_deck_id: int | None = None) -> bool:
        available = self.get_available_quantity_for_deck(card_id, exclude_deck_id=exclude_deck_id)
        return available >= quantity_needed