""" Deck Builder window for creating and editing MTG decks. """
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QComboBox, QMessageBox, QHeaderView,
    QGroupBox, QTextEdit, QSpinBox, QSplitter, QTabWidget, QFileDialog, QProgressBar
)
from PyQt5.QtGui import QFont, QColor, QCursor
from typing import Optional, List
from datetime import datetime
from src.data.database import DatabaseManager
from src.models.card import Card
from src.models.deck import Deck, DeckCard
from src.data.deck_importer import DeckImporter
from src.ui.widgets.deck_price_widget import DeckPriceWidget
from src.ui.widgets.deck_color_widget import DeckColorWidget
from src.ui.widgets.deck_insights_widget import DeckInsightsWidget
from src.ui.widgets.deck_recommendations_widget import DeckRecommendationsWidget
from src.ui.widgets.card_image_widget import CardImageWidget
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QEvent
from src.ui.widgets.card_preview_popup import CardPreviewPopup

BASIC_LANDS = {
    'Plains':   {'colors': 'W', 'type': 'Basic Land - Plains',   'text': '({T}: Add {W}.)'},
    'Island':   {'colors': 'U', 'type': 'Basic Land - Island',   'text': '({T}: Add {U}.)'},
    'Swamp':    {'colors': 'B', 'type': 'Basic Land - Swamp',    'text': '({T}: Add {B}.)'},
    'Mountain': {'colors': 'R', 'type': 'Basic Land - Mountain', 'text': '({T}: Add {R}.)'},
    'Forest':   {'colors': 'G', 'type': 'Basic Land - Forest',   'text': '({T}: Add {G}.)'},
}
class DeckBuilderWindow(QMainWindow):
    """Window for building and editing decks."""
    
    deck_saved = pyqtSignal(Deck)
    
    def __init__(self, db: DatabaseManager, deck: Optional[Deck] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.deck = deck if deck else Deck(name="New Deck", format="standard")
        self.collection_cards = []
        self.filtered_cards = []
        
        self.init_ui()
        self.load_collection()
        
        if deck and deck.id:
            self.load_deck_cards()
        
        self.update_all_displays()
        
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Deck Builder - {self.deck.name}")
        self.setGeometry(100, 100, 1600, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Deck Info
        info_layout = self.create_deck_info_section()
        main_layout.addLayout(info_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        collection_widget = self.create_collection_browser()
        splitter.addWidget(collection_widget)
        
        deck_widget = self.create_deck_list()
        splitter.addWidget(deck_widget)
        
        stats_widget = self.create_stats_panel()
        splitter.addWidget(stats_widget)
        
        splitter.setSizes([500, 600, 400])
        main_layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Deck")
        save_btn.clicked.connect(self.save_deck)
        button_layout.addWidget(save_btn)
        
        validate_btn = QPushButton("✓ Validate Deck")
        validate_btn.clicked.connect(self.validate_deck)
        button_layout.addWidget(validate_btn)
        
        export_btn = QPushButton("📄 Export Deck")
        export_btn.clicked.connect(self.export_deck)
        button_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 Import Cards")
        import_btn.clicked.connect(self.import_cards_to_deck)
        button_layout.addWidget(import_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        self.statusBar().showMessage("Ready")
        # Create once
        self.card_preview_popup = CardPreviewPopup(self)
        # Needed so QEvent.Leave is delivered to hide popup
        self.collection_table.viewport().installEventFilter(self)
    
    def create_deck_info_section(self):
        """Create deck metadata section."""
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Deck Name:"))
        self.name_input = QLineEdit(self.deck.name)
        self.name_input.textChanged.connect(self.on_deck_name_changed)
        layout.addWidget(self.name_input, stretch=2)
        
        layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['standard', 'commander', 'modern', 'pauper', 'legacy', 'vintage', 'brawl'])
        self.format_combo.setCurrentText(self.deck.format)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        layout.addWidget(self.format_combo)
        
        layout.addWidget(QLabel("Colors:"))
        self.colors_label = QLabel("-")
        self.colors_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.colors_label)
        
        return layout
    
    def create_collection_browser(self):
        """Create collection browser panel."""
        widget = QWidget()
        main_layout = QHBoxLayout()  # Change to horizontal layout
        widget.setLayout(main_layout)
    
        # Left side: collection list
        left_widget = QWidget()
        layout = QVBoxLayout()
        left_widget.setLayout(layout)
    
        header = QLabel("Your Collection")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
    
        # Basic Lands (existing code)
        basic_lands_group = QGroupBox("Basic Lands (Unlimited)")
        basic_layout = QHBoxLayout()
    
        for land_name in ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']:
            btn = QPushButton(land_name)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, name=land_name: self.add_basic_land(name))
            basic_layout.addWidget(btn)
    
        basic_lands_group.setLayout(basic_layout)
        layout.addWidget(basic_lands_group)
    
        # Search (existing code)
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.collection_search = QLineEdit()
        self.collection_search.setPlaceholderText("Card name...")
        self.collection_search.textChanged.connect(self.filter_collection)
        search_layout.addWidget(self.collection_search)
        layout.addLayout(search_layout)
    
        # Filters (existing code)
        filters_layout = QHBoxLayout()
    
        filters_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(['All', 'Creature', 'Instant', 'Sorcery', 'Enchantment', 
                                   'Artifact', 'Planeswalker', 'Land'])
        self.type_filter.currentTextChanged.connect(self.filter_collection)
        filters_layout.addWidget(self.type_filter)
    
        filters_layout.addWidget(QLabel("Color:"))
        self.color_filter = QComboBox()
        self.color_filter.addItems(['All', 'W', 'U', 'B', 'R', 'G', 'Colorless', 'Multicolor'])
        self.color_filter.currentTextChanged.connect(self.filter_collection)
        filters_layout.addWidget(self.color_filter)
    
        filters_layout.addWidget(QLabel("CMC:"))
        self.cmc_filter = QComboBox()
        self.cmc_filter.addItems(['All', '0', '1', '2', '3', '4', '5', '6', '7+'])
        self.cmc_filter.currentTextChanged.connect(self.filter_collection)
        filters_layout.addWidget(self.cmc_filter)
    
        layout.addLayout(filters_layout)
    
        # Collection table (existing code)
        self.collection_table = QTableWidget()
        self.collection_table.setColumnCount(6)
        self.collection_table.setHorizontalHeaderLabels([
            "Name", "Cost", "CMC", "Type", "Available", ""
        ])

        header = self.collection_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)          # Name
        for i in [1, 2, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
    
        layout.addWidget(self.collection_table)
    
        main_layout.addWidget(left_widget, stretch=3)
    
        # Right side: Card image preview (NEW)
        self.card_image_widget = CardImageWidget()
        main_layout.addWidget(self.card_image_widget, stretch=1)
    
        return widget
    
    def create_deck_list(self):
        """Create deck list panel."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        header_layout = QHBoxLayout()
        header = QLabel("Deck List")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header)
        header_layout.addStretch()
        self.deck_count_label = QLabel("0 cards")
        self.deck_count_label.setFont(QFont("Arial", 12))
        header_layout.addWidget(self.deck_count_label)
        layout.addLayout(header_layout)
        
        # Tabs
        self.deck_tabs = QTabWidget()
        
        self.mainboard_table = QTableWidget()
        self.setup_deck_table(self.mainboard_table, is_sideboard=False)
        self.deck_tabs.addTab(self.mainboard_table, "Mainboard (0)")
        self.mainboard_table.setMouseTracking(True)
        self.mainboard_table.cellEntered.connect(self.on_deck_table_cell_hover)
        self.mainboard_table.doubleClicked.connect(self.on_deck_table_double_click)

        
        self.sideboard_table = QTableWidget()
        self.setup_deck_table(self.sideboard_table, is_sideboard=True)
        self.deck_tabs.addTab(self.sideboard_table, "Sideboard (0)")
        self.sideboard_table.setMouseTracking(True)
        self.sideboard_table.cellEntered.connect(self.on_deck_table_cell_hover)
        self.sideboard_table.doubleClicked.connect(self.on_deck_table_double_click)

        layout.addWidget(self.deck_tabs)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setPlainText(self.deck.description or "")
        layout.addWidget(self.description_text)
        
        return widget
    
    def setup_deck_table(self, table: QTableWidget, is_sideboard: bool):
        """Configure a deck card table."""
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Qty", "Name", "Cost", "Type", ""])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setMouseTracking(True)
        table.cellDoubleClicked.connect(
            lambda row, col: self.remove_card_from_deck_from_table(row, is_sideboard)
        )
        header = table.horizontalHeader()
        # Name stretches, others size-to-contents
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in [0, 2, 3, 4]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
    
    def create_stats_panel(self):
        """Create deck statistics panel."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
    
        # Create tabs for different stat views
        stats_tabs = QTabWidget()
    
        # === TAB 1: Basic Stats (existing) ===
        basic_stats_widget = QWidget()
        basic_layout = QVBoxLayout()
        basic_stats_widget.setLayout(basic_layout)
    
        header = QLabel("Deck Statistics")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        basic_layout.addWidget(header)
    
        # Card counts
        counts_group = QGroupBox("Card Counts")
        counts_layout = QVBoxLayout()
        self.mainboard_count_label = QLabel("Mainboard: 0")
        self.sideboard_count_label = QLabel("Sideboard: 0")
        self.creatures_count_label = QLabel("Creatures: 0")
        self.lands_count_label = QLabel("Lands: 0")
        self.spells_count_label = QLabel("Spells: 0")
        counts_layout.addWidget(self.mainboard_count_label)
        counts_layout.addWidget(self.sideboard_count_label)
        counts_layout.addWidget(self.creatures_count_label)
        counts_layout.addWidget(self.lands_count_label)
        counts_layout.addWidget(self.spells_count_label)
        counts_group.setLayout(counts_layout)
        basic_layout.addWidget(counts_group)
    
        # Mana curve
        curve_group = QGroupBox("Mana Curve (Non-Lands)")
        self.curve_layout = QVBoxLayout()
        curve_group.setLayout(self.curve_layout)
        basic_layout.addWidget(curve_group)
    
        # Type distribution
        types_group = QGroupBox("Card Types")
        self.types_layout = QVBoxLayout()
        types_group.setLayout(self.types_layout)
        basic_layout.addWidget(types_group)
    
        # Average CMC
        self.avg_cmc_label = QLabel("Average CMC: 0.0")
        self.avg_cmc_label.setFont(QFont("Arial", 11))
        basic_layout.addWidget(self.avg_cmc_label)
    
        basic_layout.addStretch()
    
        stats_tabs.addTab(basic_stats_widget, "📊 Stats")
    
        # === TAB 2: Price Analysis
        self.price_widget = DeckPriceWidget()
        stats_tabs.addTab(self.price_widget, "💰 Price")

        # === TAB 3: Color Analysis
        self.color_widget = DeckColorWidget()
        stats_tabs.addTab(self.color_widget, "🎨 Colors")

        # === TAB 4: Deck Insights
        self.insights_widget = DeckInsightsWidget()
        stats_tabs.addTab(self.insights_widget, "🔍 Insights")

        # === TAB 5: Recommendations (NEW) ===
        self.recommendations_widget = DeckRecommendationsWidget()
        self.recommendations_widget.card_selected.connect(self.add_card_to_deck)
        stats_tabs.addTab(self.recommendations_widget, "💡 Suggestions")
    
        layout.addWidget(stats_tabs)
    
        return widget
    
    def load_collection(self):
        """Load all cards from collection."""
        self.collection_cards = self.db.get_all_cards()
        self.filter_collection()
        self.statusBar().showMessage(f"Loaded {len(self.collection_cards)} cards from collection")
    
    def filter_collection(self):
        """Filter collection based on search and filters."""
        query = self.collection_search.text().strip().lower()
        type_filter = self.type_filter.currentText()
        color_filter = self.color_filter.currentText()
        cmc_filter = self.cmc_filter.currentText()
        
        self.filtered_cards = []
        
        for card in self.collection_cards:
            # Name filter
            if query and query not in card.name.lower():
                continue
            
            # Type filter
            if type_filter != 'All':
                types = card.get_types_list()
                if type_filter not in types:
                    continue
            
            # Color filter
            if color_filter != 'All':
                colors = card.get_colors_list()
                if color_filter == 'Colorless':
                    if len(colors) > 0:
                        continue
                elif color_filter == 'Multicolor':
                    if len(colors) <= 1:
                        continue
                else:
                    if color_filter not in colors:
                        continue
            
            # CMC filter
            if cmc_filter != 'All' and card.cmc is not None:
                if cmc_filter == '7+':
                    if card.cmc < 7:
                        continue
                else:
                    if int(card.cmc) != int(cmc_filter):
                        continue
            
            self.filtered_cards.append(card)
        
        self.populate_collection_table()

    def populate_collection_table(self):
        """Populate collection table with filtered cards."""
        self.collection_table.setRowCount(len(self.filtered_cards))

        for row, card in enumerate(self.filtered_cards):
            # Name (store Card for hover)
            name_item = QTableWidgetItem(card.name or "")
            name_item.setData(Qt.UserRole, card)  # PyQt5 role
            self.collection_table.setItem(row, 0, name_item)

            # Mana Cost
            cost = card.mana_cost if card.mana_cost else "-"
            self.collection_table.setItem(row, 1, QTableWidgetItem(cost))

            # CMC
            cmc = str(int(card.cmc)) if card.cmc is not None else "-"
            self.collection_table.setItem(row, 2, QTableWidgetItem(cmc))

            # Type
            type_line = card.type_line if card.type_line else "-"
            self.collection_table.setItem(row, 3, QTableWidgetItem(type_line))

            # Available
            available = self.get_available_quantity(card)
            qty_item = QTableWidgetItem(str(available))
            qty_item.setTextAlignment(Qt.AlignCenter)
            if available == 0:
                qty_item.setBackground(QColor('#ffcccc'))
            self.collection_table.setItem(row, 4, qty_item)

            # Add button
            add_btn = QPushButton("Add →")
            add_btn.clicked.connect(lambda checked, c=card: self.add_card_to_deck(c))
            self.collection_table.setCellWidget(row, 5, add_btn)
    
    def populate_deck_table(self, table: QTableWidget, cards: List[DeckCard]):
        """Populate a deck table with cards."""
        # Sort (lands first, then creatures, then others), then CMC, then name
        sorted_cards = sorted(cards, key=lambda dc: (
            0 if dc.card.is_land() else 1 if dc.card.is_creature() else 2,
            dc.card.cmc if dc.card.cmc is not None else 0,
            dc.card.name or ""
        ))
        table.setRowCount(len(sorted_cards))
        for row, deck_card in enumerate(sorted_cards):
            card = deck_card.card
            # Qty -> column 0
            qty_item = QTableWidgetItem(str(deck_card.quantity))
            qty_item.setTextAlignment(Qt.AlignCenter)  # PyQt5
            table.setItem(row, 0, qty_item)
            # Name -> column 1 (store the Card in UserRole for hover)
            name = card.name or ""
            if deck_card.is_commander:
                name = f"⭐ {name} (Commander)"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, card)       # PyQt5 role
            table.setItem(row, 1, name_item)
            # Cost -> column 2
            cost = card.mana_cost if card.mana_cost else "-"
            table.setItem(row, 2, QTableWidgetItem(cost))
            # Type -> column 3
            type_line = card.type_line if card.type_line else "-"
            table.setItem(row, 3, QTableWidgetItem(type_line))
            # Remove button -> column 4
            btn = QPushButton("Remove")
            btn.clicked.connect(lambda checked, c=card, sb=deck_card.in_sideboard:
                                self.remove_card_from_deck(c, from_sideboard=sb))
            table.setCellWidget(row, 4, btn)

    def load_deck_cards(self):
        """Load existing deck cards."""
        full_deck = self.db.get_deck(self.deck.id)
        if full_deck:
            self.deck = full_deck
            self.name_input.setText(self.deck.name)
            self.format_combo.setCurrentText(self.deck.format)
            self.description_text.setPlainText(self.deck.description or "")
    
    def populate_deck_table(self, table: QTableWidget, cards: List[DeckCard]):
        """Populate a deck table with cards."""
        # Sort by type then name
        sorted_cards = sorted(cards, key=lambda dc: (
            0 if dc.card.is_land() else 1 if dc.card.is_creature() else 2,
            dc.card.cmc if dc.card.cmc else 0,
            dc.card.name
        ))
        
        table.setRowCount(len(sorted_cards))
        
        for row, deck_card in enumerate(sorted_cards):
            card = deck_card.card
            
            # Quantity
            qty_item = QTableWidgetItem(str(deck_card.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, qty_item)
            
            # Name (with commander indicator)
            name = card.name
            if deck_card.is_commander:
                name = f"⭐ {name} (Commander)"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, card)  # ADD THIS LINE
            table.setItem(row, 1, name_item)
            
            # Mana Cost
            cost = card.mana_cost if card.mana_cost else "-"
            table.setItem(row, 2, QTableWidgetItem(cost))
            
            # Type
            type_line = card.type_line if card.type_line else "-"
            table.setItem(row, 3, QTableWidgetItem(type_line))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, c=card, sb=deck_card.in_sideboard: 
                                      self.remove_card_from_deck(c, from_sideboard=sb))
            table.setCellWidget(row, 4, remove_btn)
    
    def update_deck_display(self):
        """Update deck list tables."""
        mainboard = self.deck.get_mainboard_cards()
        sideboard = self.deck.get_sideboard_cards()
        
        self.populate_deck_table(self.mainboard_table, mainboard)
        self.populate_deck_table(self.sideboard_table, sideboard)
        
        # Update tab labels
        self.deck_tabs.setTabText(0, f"Mainboard ({sum(dc.quantity for dc in mainboard)})")
        self.deck_tabs.setTabText(1, f"Sideboard ({sum(dc.quantity for dc in sideboard)})")
        
        # Update card count
        total = self.deck.total_cards()
        self.deck_count_label.setText(f"{total} cards")
    
    def update_stats_display(self):
        """Update statistics panel."""
        mainboard = self.deck.get_mainboard_cards()
        
        # Card counts
        mainboard_count = sum(dc.quantity for dc in mainboard)
        sideboard_count = self.deck.sideboard_count()
        
        creatures = sum(dc.quantity for dc in mainboard if dc.card.is_creature())
        lands = sum(dc.quantity for dc in mainboard if dc.card.is_land())
        spells = sum(dc.quantity for dc in mainboard if dc.card.is_instant_or_sorcery())
        
        self.mainboard_count_label.setText(f"Mainboard: {mainboard_count}")
        self.sideboard_count_label.setText(f"Sideboard: {sideboard_count}")
        self.creatures_count_label.setText(f"Creatures: {creatures}")
        self.lands_count_label.setText(f"Lands: {lands}")
        self.spells_count_label.setText(f"Instants/Sorceries: {spells}")
        
        # Mana curve
        curve = self.deck.get_mana_curve()
        self.update_mana_curve_display(curve)
        
        # Type distribution
        type_dist = self.deck.get_type_distribution()
        self.update_type_distribution_display(type_dist)
        
        # Average CMC
        non_lands = [dc for dc in mainboard if not dc.card.is_land()]
        if non_lands:
            total_cmc = sum(dc.card.cmc * dc.quantity for dc in non_lands if dc.card.cmc is not None)
            total_cards = sum(dc.quantity for dc in non_lands)
            avg_cmc = total_cmc / total_cards if total_cards > 0 else 0
            self.avg_cmc_label.setText(f"Average CMC: {avg_cmc:.2f}")
        else:
            self.avg_cmc_label.setText("Average CMC: 0.0")
        
        # Update colors
        colors = self.deck.get_colors()
        self.colors_label.setText(','.join(colors) if colors else "Colorless")
        
        # Update prices
        self.price_widget.set_deck(self.deck)

        # UPDATE COLOR WIDGET (ADD THIS)
        self.color_widget.set_deck(self.deck)

        # UPDATE INSIGHTS WIDGET (ADD THIS)
        self.insights_widget.set_deck(self.deck)
    
    def update_mana_curve_display(self, curve: dict):
        """Update mana curve visualization."""
        # Clear existing
        while self.curve_layout.count():
            item = self.curve_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not curve:
            self.curve_layout.addWidget(QLabel("No cards"))
            return
        
        max_count = max(curve.values()) if curve else 1
        
        for cmc in range(8):
            count = curve.get(cmc, 0)
            label_text = f"{cmc}{'+'if cmc==7 else ''}: {count}"
            
            # Create progress bar
            bar_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(50)
            bar_layout.addWidget(label)
            
            bar = QProgressBar()
            bar.setMaximum(max_count)
            bar.setValue(count)
            bar.setTextVisible(False)
            bar.setMaximumHeight(15)
            bar_layout.addWidget(bar)
            
            container = QWidget()
            container.setLayout(bar_layout)
            self.curve_layout.addWidget(container)
    
    def update_type_distribution_display(self, type_dist: dict):
        """Update type distribution display."""
        # Clear existing
        while self.types_layout.count():
            item = self.types_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not type_dist:
            self.types_layout.addWidget(QLabel("No cards"))
            return
        
        for card_type, count in sorted(type_dist.items(), key=lambda x: -x[1]):
            label = QLabel(f"{card_type}: {count}")
            self.types_layout.addWidget(label)
    
    def update_all_displays(self):
        """Update all UI displays."""
        self.update_deck_display()
        self.update_stats_display()
        self.populate_collection_table()  # Refresh available quantities
        self.recommendations_widget.set_deck_and_collection(self.deck, self.collection_cards)
    
    def get_available_quantity(self, card: Card) -> int:
        """Get available quantity of a card (collection - already in deck)."""
        # Basic lands are unlimited
        if card.name in BASIC_LANDS and 'Basic' in (card.type_line or ''):
            return 999
    
        # Count how many are in the current deck
        in_deck = sum(dc.quantity for dc in self.deck.cards if dc.card.id == card.id)
        return max(0, card.quantity - in_deck)
    
    def add_card_to_deck(self, card: Card, to_sideboard: bool = False):
        """Add a card to the deck."""
        # Basic lands are unlimited
        is_basic_land = card.name in BASIC_LANDS and 'Basic' in (card.type_line or '')
    
        if not is_basic_land:
            available = self.get_available_quantity(card)
        
            if available <= 0:
                QMessageBox.warning(self, "Unavailable", f"No copies of '{card.name}' available in collection.")
                return
    
        self.deck.add_card(card, quantity=1, in_sideboard=to_sideboard)
        self.update_all_displays()
        self.statusBar().showMessage(f"Added {card.name} to {'sideboard' if to_sideboard else 'deck'}")
    
    def add_basic_land(self, land_name: str):
        """Add a basic land to the deck (unlimited, not from collection)."""
        # Create a basic land card object
        land_info = BASIC_LANDS[land_name]
    
        # Check if we already have this basic land in collection
        existing = None
        for card in self.collection_cards:
            if card.name == land_name and 'Basic' in (card.type_line or ''):
                existing = card
                break
    
        if existing:
            # Use the existing card from collection
            basic_land = existing
        else:
            # Create a virtual basic land card
            basic_land = Card(
                name=land_name,
                set_code='BASIC',
                collector_number='0',
                rarity='common',
                mana_cost='',
                cmc=0.0,
                colors=land_info['colors'],
                color_identity=land_info['colors'],
                type_line=land_info['type'],
                card_types='Land,Basic',
                subtypes=land_name,
                oracle_text=land_info['text'],
                quantity=999,  # Unlimited
                id=-ord(land_name[0])  # Negative ID to mark as virtual
            )
    
        # Add to deck (don't check availability for basic lands)
        to_sideboard = self.deck_tabs.currentIndex() == 1  # Check if sideboard tab is active
        self.deck.add_card(basic_land, quantity=1, in_sideboard=to_sideboard)
        self.update_all_displays()
        self.statusBar().showMessage(f"Added {land_name} to {'sideboard' if to_sideboard else 'deck'}")

    def add_card_to_deck_from_table(self, row, column):
        """Add card from collection table double-click."""
        if row < len(self.filtered_cards):
            card = self.filtered_cards[row]
            self.add_card_to_deck(card)
    
    def remove_card_from_deck(self, card: Card, from_sideboard: bool = False):
        """Remove a card from the deck."""
        if self.deck.remove_card(card, quantity=1, from_sideboard=from_sideboard):
            self.update_all_displays()
            self.statusBar().showMessage(f"Removed {card.name} from {'sideboard' if from_sideboard else 'deck'}")
    
    def remove_card_from_deck_from_table(self, row, is_sideboard: bool):
        """Remove card from deck table double-click."""
        cards = self.deck.get_sideboard_cards() if is_sideboard else self.deck.get_mainboard_cards()
        
        # Apply same sorting as populate
        sorted_cards = sorted(cards, key=lambda dc: (
            0 if dc.card.is_land() else 1 if dc.card.is_creature() else 2,
            dc.card.cmc if dc.card.cmc else 0,
            dc.card.name
        ))
        
        if row < len(sorted_cards):
            deck_card = sorted_cards[row]
            self.remove_card_from_deck(deck_card.card, from_sideboard=is_sideboard)
    
    def on_deck_name_changed(self):
        """Handle deck name change."""
        self.deck.name = self.name_input.text()
        self.setWindowTitle(f"Deck Builder - {self.deck.name}")
    
    def on_format_changed(self):
        """Handle format change."""
        self.deck.format = self.format_combo.currentText()
        self.statusBar().showMessage(f"Format changed to {self.deck.format}")
    
    def save_deck(self):
        """Save the deck to database."""
        if not self.deck.name.strip():
            QMessageBox.warning(self, "Invalid Name", "Please enter a deck name.")
            return
        
        self.deck.description = self.description_text.toPlainText()
        self.deck.update_colors()
        
        try:
            if self.deck.id:
                self.db.update_deck(self.deck)
                message = f"Deck '{self.deck.name}' updated successfully!"
            else:
                deck_id = self.db.create_deck(self.deck)
                self.deck.id = deck_id
                message = f"Deck '{self.deck.name}' created successfully!"
            
            QMessageBox.information(self, "Success", message)
            self.deck_saved.emit(self.deck)
            self.statusBar().showMessage("Deck saved")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save deck:\n{str(e)}")
    
    def validate_deck(self):
        """Validate deck against format rules."""
        errors = self.deck.validate()
        
        if not errors:
            QMessageBox.information(self, "Valid Deck", 
                                  f"✓ Deck is valid for {self.deck.format} format!")
        else:
            error_text = "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Validation Errors", 
                              f"Deck has the following issues:\n\n{error_text}")
    
    def export_deck(self):
        """Export deck to text file."""
        if not self.deck.name:
            QMessageBox.warning(self, "No Deck", "Please create a deck first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Deck",
            f"{self.deck.name}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Deck: {self.deck.name}\n")
                f.write(f"Format: {self.deck.format}\n")
                f.write(f"Colors: {self.colors_label.text()}\n")
                
                if self.deck.description:
                    f.write(f"\nDescription:\n{self.deck.description}\n")
                
                f.write(f"\n// Mainboard ({self.deck.mainboard_count()})\n")
                for dc in sorted(self.deck.get_mainboard_cards(), key=lambda x: x.card.name):
                    f.write(f"{dc.quantity} {dc.card.name}\n")
                
                sideboard = self.deck.get_sideboard_cards()
                if sideboard:
                    f.write(f"\n// Sideboard ({self.deck.sideboard_count()})\n")
                    for dc in sorted(sideboard, key=lambda x: x.card.name):
                        f.write(f"{dc.quantity} {dc.card.name}\n")
            
            QMessageBox.information(self, "Success", f"Deck exported to:\n{file_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export deck:\n{str(e)}")

    def import_cards_to_deck(self):
        """Import cards from file into current deck."""
        from PyQt5.QtWidgets import QFileDialog
    
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Cards to Deck",
            "",
            "Deck Files (*.txt *.csv);;Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
    
        if not file_path:
            return
    
        try:
            importer = DeckImporter(self.db)
            imported_deck, warnings = importer.import_deck(file_path, "temp", self.deck.format)
        
            # Add all cards from imported deck to current deck
            for deck_card in imported_deck.cards:
                # Check if card already exists
                existing = None
                for dc in self.deck.cards:
                    if dc.card.name == deck_card.card.name and dc.in_sideboard == deck_card.in_sideboard:
                        existing = dc
                        break
            
                if existing:
                    existing.quantity += deck_card.quantity
                else:
                    self.deck.cards.append(deck_card)
        
            self.update_all_displays()
        
            # Show results
            message = f"Imported {len(imported_deck.cards)} card types\n"
            message += f"Total cards added: {imported_deck.total_cards()}\n"
        
            if warnings:
                message += f"\n⚠ {len(warnings)} warnings (check status bar)"
                for warning in warnings[:5]:
                    self.statusBar().showMessage(warning)
        
            QMessageBox.information(self, "Import Complete", message)
        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import:\n{str(e)}")

    def on_collection_cell_hover(self, row, column):
        """Show floating popup when hovering collection table."""
        if row < 0 or row >= self.collection_table.rowCount():
            if hasattr(self, "card_preview_popup"):
                self.card_preview_popup.hide_popup()
            return
        name_item = self.collection_table.item(row, 0)
        if not name_item:
            return
        card = name_item.data(Qt.UserRole)  # PyQt5 role
        if not card:
            return
        cursor_pos = QCursor.pos()
        self.card_preview_popup.show_card(card, cursor_pos)

    def on_deck_table_cell_hover(self, row, column):
        """Update right-side image when hovering deck tables."""
        table = self.mainboard_table if self.deck_tabs.currentIndex() == 0 else self.sideboard_table
        if row < 0 or row >= table.rowCount():
            return

        # Read Card from the Name column
        item = table.item(row, 1)
        if not item:
            return

        card = item.data(Qt.UserRole)   # PyQt5 role
        if card:
            self.card_image_widget.set_card(card)

    def on_collection_double_click(self, index):
        """Add card to deck when double-clicking in collection."""
        row = index.row()
        if row < 0 or row >= self.collection_table.rowCount():
            return
        name_item = self.collection_table.item(row, 0)
        if name_item:
            card = name_item.data(Qt.UserRole)
            if card:
                self.add_card_to_deck(card)

    def on_deck_table_double_click(self, index):
        """Remove card from deck when double-clicking in deck table."""
        row = index.row()
    
        # Determine which table was clicked
        sender = self.sender()
        is_sideboard = (sender == self.sideboard_table)
    
        if row < 0 or row >= sender.rowCount():
            return
    
        # Get card from the Name column (column 1)
        name_item = sender.item(row, 1)
        if name_item:
            card = name_item.data(Qt.ItemDataRole.UserRole)
            if card:
                self.remove_card_from_deck(card, from_sideboard=is_sideboard)

    def eventFilter(self, obj, event):
        if obj == self.collection_table.viewport():
            if event.type() == QEvent.Leave:   # PyQt5
                if hasattr(self, "card_preview_popup"):
                    self.card_preview_popup.hide_popup()
        return super().eventFilter(obj, event)