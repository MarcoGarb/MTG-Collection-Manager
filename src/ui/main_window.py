"""
Main application window for MTG Collection Manager.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QFileDialog,
    QMessageBox, QHeaderView, QGroupBox, QGridLayout, QStackedWidget,
    QProgressDialog, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.data.database import DatabaseManager
from src.data.importer import CSVImporter
from src.api.price_updater import PriceUpdater
from src.ui.card_detail_dialog import CardDetailDialog
from src.ui.gallery_view import GalleryView
from src.ui.filter_panel import FilterPanel
from PyQt5.QtGui import QColor
from src.ui.deck_builder_window import DeckBuilderWindow
from src.ui.deck_list_dialog import DeckListDialog
from src.ui.cube_builder_window import CubeBuilderWindow
from src.ui.widgets.card_preview_popup import CardPreviewPopup

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.db.connect()
        self.db.initialize_schema()
        self.price_updater = PriceUpdater(self.db)
        
        # View state
        self.current_view = "table"  # "table" or "gallery"
        
        self.init_ui()
        self.load_collection()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("MTG Collection Manager")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # === TOP SECTION: Stats ===
        stats_group = self.create_stats_section()
        main_layout.addWidget(stats_group)
        
        # === MIDDLE SECTION: Search and Controls ===
        controls_layout = QHBoxLayout()
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search cards by name...")
        self.search_input.textChanged.connect(self.search_cards)
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.search_input, stretch=3)
        
        # View toggle button
        self.view_toggle_btn = QPushButton("Switch to Gallery View")
        self.view_toggle_btn.clicked.connect(self.toggle_view)
        controls_layout.addWidget(self.view_toggle_btn)
        
        # Filter toggle button
        self.filter_toggle_btn = QPushButton("Show Filters")
        self.filter_toggle_btn.setCheckable(True)
        self.filter_toggle_btn.clicked.connect(self.toggle_filters)
        controls_layout.addWidget(self.filter_toggle_btn)

        # Import button
        import_btn = QPushButton("Import CSV")
        import_btn.clicked.connect(self.import_csv)
        controls_layout.addWidget(import_btn)
        
        # Update prices button
        update_prices_btn = QPushButton("Update Prices")
        update_prices_btn.clicked.connect(self.update_prices)
        controls_layout.addWidget(update_prices_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_collection)
        controls_layout.addWidget(refresh_btn)
        
        # Clear database button
        clear_btn = QPushButton("Clear Database")
        clear_btn.clicked.connect(self.clear_database)
        controls_layout.addWidget(clear_btn)
        
        main_layout.addLayout(controls_layout)

        # Deck Builder button (ADD THIS)
        deck_builder_btn = QPushButton("⚔️ Deck Builder")
        deck_builder_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        deck_builder_btn.clicked.connect(self.open_deck_builder)
        controls_layout.addWidget(deck_builder_btn)
        
        # Cube Builder button
        cube_builder_btn = QPushButton("🎲 Cube Builder")
        cube_builder_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        cube_builder_btn.clicked.connect(self.open_cube_builder)
        controls_layout.addWidget(cube_builder_btn)

        # Filter toggle button (this should already exist)
        self.filter_toggle_btn = QPushButton("Show Filters")
        
        # === VIEW SECTION: Stacked widget for table/gallery toggle ===
        self.view_stack = QStackedWidget()
        
        # Table view
        self.card_table = QTableWidget()
        self.setup_table()
        self.view_stack.addWidget(self.card_table)
        self.card_preview_popup = CardPreviewPopup()
        
        # Gallery view
        self.gallery_view = GalleryView()
        self.gallery_view.card_clicked.connect(self.show_card_details_from_object)
        self.view_stack.addWidget(self.gallery_view)

        # === CONTENT SECTION: Filters + Views ===
        content_layout = QHBoxLayout()

        # Filter panel (collapsible)
        self.filter_panel = FilterPanel()
        self.filter_panel.filters_changed.connect(self.apply_filters)
        self.filter_panel.setVisible(False)  # Hidden by default
        content_layout.addWidget(self.filter_panel)

        # Views
        content_layout.addWidget(self.view_stack, stretch=1)

        main_layout.addLayout(content_layout)

        main_layout.addWidget(self.view_stack)
        
        # Status bar
        self.statusBar().showMessage("Ready")

        self.card_preview_popup = CardPreviewPopup()  
        
    def create_stats_section(self):
        """Create the statistics display section."""
        stats_group = QGroupBox("Collection Statistics")
        stats_layout = QGridLayout()
        
        # Create stat labels
        self.stat_total = QLabel("0")
        self.stat_unique = QLabel("0")
        self.stat_value = QLabel("$0.00")
        self.stat_commons = QLabel("0")
        self.stat_uncommons = QLabel("0")
        self.stat_rares = QLabel("0")
        self.stat_mythics = QLabel("0")
        
        # Style stat labels
        for label in [self.stat_total, self.stat_unique, self.stat_value,
                      self.stat_commons, self.stat_uncommons, self.stat_rares, self.stat_mythics]:
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            label.setFont(font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to layout
        stats_layout.addWidget(QLabel("Total Cards:"), 0, 0)
        stats_layout.addWidget(self.stat_total, 1, 0)
        
        stats_layout.addWidget(QLabel("Unique Cards:"), 0, 1)
        stats_layout.addWidget(self.stat_unique, 1, 1)
        
        stats_layout.addWidget(QLabel("Total Value:"), 0, 2)
        stats_layout.addWidget(self.stat_value, 1, 2)
        
        stats_layout.addWidget(QLabel("Commons:"), 0, 3)
        stats_layout.addWidget(self.stat_commons, 1, 3)
        
        stats_layout.addWidget(QLabel("Uncommons:"), 0, 4)
        stats_layout.addWidget(self.stat_uncommons, 1, 4)
        
        stats_layout.addWidget(QLabel("Rares:"), 0, 5)
        stats_layout.addWidget(self.stat_rares, 1, 5)
        
        stats_layout.addWidget(QLabel("Mythics:"), 0, 6)
        stats_layout.addWidget(self.stat_mythics, 1, 6)
        
        stats_group.setLayout(stats_layout)
        return stats_group
        
    def setup_table(self):
        """Configure the card table."""
        columns = [
            "Name", "Mana Cost", "CMC", "Colors", "Type", 
            "Set", "Rarity", "Foil", "Condition", "Qty", "Price", "Value"
        ]
        self.card_table.setColumnCount(len(columns))
        self.card_table.setHorizontalHeaderLabels(columns)
    
        # Make table read-only and select entire rows
        self.card_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.card_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.card_table.setMouseTracking(True)
        self.card_table.cellEntered.connect(self.on_collection_table_hover) 
        self.card_table.viewport().installEventFilter(self)
        # Enable double-click to view details
        self.card_table.cellDoubleClicked.connect(self.show_card_details)
    
        # Stretch the name column, fit others
        header = self.card_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Type
        for i in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11]:  # Other columns
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        

    def toggle_view(self):
        """Toggle between table and gallery view."""
        if self.current_view == "table":
            self.current_view = "gallery"
            self.view_stack.setCurrentIndex(1)
            self.view_toggle_btn.setText("Switch to Table View")
            # This is correct:
            self.load_gallery_view()
        else:
            self.current_view = "table"
            self.view_stack.setCurrentIndex(0)
            self.view_toggle_btn.setText("Switch to Gallery View")

    def load_collection(self):
        """Load all cards from database into the current view."""
        self.statusBar().showMessage("Loading collection...")
        
        cards = self.db.get_all_cards()
        
        if self.current_view == "table":
            self.populate_table(cards)
        else:
            self.gallery_view.set_cards(cards)
            
        self.update_stats()
        
        self.statusBar().showMessage(f"Loaded {len(cards)} cards")
        
    def load_gallery_view(self):
        """Load cards into gallery view."""
        query = self.search_input.text().strip()
        
        if query:
            cards = self.db.search_cards(query)
        else:
            cards = self.db.get_all_cards()
            
        self.gallery_view.set_cards(cards)
    
    def get_rarity_color(self, rarity: str) -> str:
        """Get background color for rarity."""
        rarity_colors = {
            'common': '#1a1a1a',
            'uncommon': '#c0c0c0',
            'rare': '#ffd700',
            'mythic': '#ff8c00'
        }
        return rarity_colors.get(rarity.lower(), '#1a1a1a')    

    def populate_table(self, cards):
        """Populate the table with card data."""
        self.card_table.setRowCount(0)
        self.card_table.setRowCount(len(cards))
    
        for row, card in enumerate(cards):
            # Name
            name_item = QTableWidgetItem(card.name)
            name_item.setData(Qt.ItemDataRole.UserRole, card)
            self.card_table.setItem(row, 0, name_item)
        
            # Mana Cost
            mana_cost = card.mana_cost if card.mana_cost else "-"
            self.card_table.setItem(row, 1, QTableWidgetItem(mana_cost))
        
            # CMC
            cmc = str(int(card.cmc)) if card.cmc is not None else "-"
            self.card_table.setItem(row, 2, QTableWidgetItem(cmc))
        
            # Colors
            colors = card.colors if card.colors else "C"  # C for colorless
            self.card_table.setItem(row, 3, QTableWidgetItem(colors))
        
            # Type Line
            type_line = card.type_line if card.type_line else "-"
            self.card_table.setItem(row, 4, QTableWidgetItem(type_line))
        
            # Set
            self.card_table.setItem(row, 5, QTableWidgetItem(card.set_code.upper()))
        
            # Rarity (with color coding)
            rarity = card.rarity.capitalize() if card.rarity else "-"
            rarity_item = QTableWidgetItem(rarity)
            if card.rarity:
                color = self.get_rarity_color(card.rarity)
                rarity_item.setBackground(QColor(color))
                if card.rarity.lower() in ['common', 'mythic']:
                    rarity_item.setForeground(QColor('white'))
            self.card_table.setItem(row, 6, rarity_item)
        
            # Foil
            self.card_table.setItem(row, 7, QTableWidgetItem("Yes" if card.foil else "No"))
        
            # Condition
            condition = card.condition.replace('_', ' ').title() if card.condition else "-"
            self.card_table.setItem(row, 8, QTableWidgetItem(condition))
        
            # Quantity
            self.card_table.setItem(row, 9, QTableWidgetItem(str(card.quantity)))
        
            # Price
            price_str = f"${card.current_price:.2f}" if card.current_price else "-"
            self.card_table.setItem(row, 10, QTableWidgetItem(price_str))
        
            # Total Value
            if card.current_price:
                total_value = card.current_price * card.quantity
                value_str = f"${total_value:.2f}"
            else:
                value_str = "-"
            self.card_table.setItem(row, 11, QTableWidgetItem(value_str))

    def update_stats(self):
        """Update the statistics display."""
        stats = self.db.get_collection_stats()
        
        self.stat_total.setText(str(stats['total_cards']))
        self.stat_unique.setText(str(stats['unique_cards']))
        self.stat_value.setText(f"${stats['total_value']:.2f}")
        
        by_rarity = stats['by_rarity']
        self.stat_commons.setText(str(by_rarity.get('common', 0)))
        self.stat_uncommons.setText(str(by_rarity.get('uncommon', 0)))
        self.stat_rares.setText(str(by_rarity.get('rare', 0)))
        self.stat_mythics.setText(str(by_rarity.get('mythic', 0)))
        
    def search_cards(self):
        """Search cards based on search input."""
        query = self.search_input.text().strip()
    
        # If filters are visible, apply them
        if self.filter_panel.isVisible():
            self.apply_filters()
            return
    
        # Otherwise do simple name search
        if not query:
            self.load_collection()
            return
        
        cards = self.db.search_cards(query)
    
        if self.current_view == "table":
            self.populate_table(cards)
        else:
            self.gallery_view.set_cards(cards)
        
        self.statusBar().showMessage(f"Found {len(cards)} cards matching '{query}'")
        
    def show_card_details(self, row, column):
        """Show detailed view of selected card from table."""
        query = self.search_input.text().strip()
        
        if query:
            cards = self.db.search_cards(query)
        else:
            cards = self.db.get_all_cards()
            
        if row < len(cards):
            card = cards[row]
            dialog = CardDetailDialog(card, self)
            dialog.exec()
            
    def show_card_details_from_object(self, card):
        """Show detailed view of card from gallery."""
        dialog = CardDetailDialog(card, self)
        dialog.exec()
        
    def import_csv(self):
        """Import cards from a CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "data/",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            self.statusBar().showMessage("Importing CSV...")
            
            # Import cards
            cards = CSVImporter.import_from_manabox(file_path)
            
            # Save to database
            added = 0
            for card in cards:
                self.db.add_card(card)
                added += 1
                
            # Refresh display
            self.load_collection()
            
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {added} cards!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import CSV:\n{str(e)}"
            )
            self.statusBar().showMessage("Import failed")
            
    def update_prices(self):
        """Update all card prices from Scryfall API."""
        reply = QMessageBox.question(
            self,
            "Update Prices",
            f"This will fetch current prices from Scryfall for all cards in your collection.\n\n"
            f"This may take several minutes depending on collection size.\n\n"
            f"Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Get total cards
        cards = self.db.get_all_cards()
        total = len(cards)
        
        # Create progress dialog
        progress = QProgressDialog("Updating prices from Scryfall...", "Cancel", 0, total, self)
        progress.setWindowTitle("Price Update")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        
        def progress_callback(current, total, card_name):
            progress.setValue(current)
            progress.setLabelText(f"Updating {current}/{total}: {card_name}")
            
            # Allow cancel
            if progress.wasCanceled():
                raise InterruptedError("Update cancelled by user")
        
        try:
            stats = self.price_updater.update_all_prices(progress_callback)
            
            progress.close()
            
            # Refresh display
            self.load_collection()
            
            # Show results
            QMessageBox.information(
                self,
                "Update Complete",
                f"Price update finished!\n\n"
                f"✓ Updated: {stats['updated']}\n"
                f"⚠ Not found: {stats['not_found']}\n"
                f"⚠ No price available: {stats['no_price']}\n"
                f"✗ Errors: {stats['errors']}"
            )
            
        except InterruptedError:
            progress.close()
            QMessageBox.information(self, "Cancelled", "Price update cancelled.")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Error updating prices:\n{str(e)}")
            
    def clear_database(self):
        """Clear all cards from the database."""
        reply = QMessageBox.question(
            self,
            "Clear Database",
            "Are you sure you want to delete all cards from the collection?\nThis cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_collection()
            self.load_collection()
            QMessageBox.information(self, "Success", "Collection cleared!")
     
    def open_deck_builder(self):
        """Open the deck builder window."""
        # Create deck list dialog first
        dialog = DeckListDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Dialog will handle opening the builder
            pass

    def open_deck_builder_new(self):
        """Open deck builder for a new deck."""
        builder = DeckBuilderWindow(self.db, parent=self)
        builder.deck_saved.connect(self.on_deck_saved)
        builder.show()

    def open_deck_builder_edit(self, deck: 'Deck'):
        """Open deck builder for editing existing deck."""
        builder = DeckBuilderWindow(self.db, deck=deck, parent=self)
        builder.deck_saved.connect(self.on_deck_saved)
        builder.show()

    def on_deck_saved(self, deck):
        """Handle deck saved signal."""
        QMessageBox.information(self, "Success", f"Deck '{deck.name}' saved successfully!")

    def open_cube_builder(self):
        """Open the cube builder window."""
        builder = CubeBuilderWindow(self.db, parent=self)
        builder.cube_saved.connect(self.on_cube_saved)
        builder.show()

    def on_cube_saved(self, cube):
        """Handle cube saved signal."""
        QMessageBox.information(self, "Success", f"Cube '{cube.name}' saved successfully!")

    def closeEvent(self, event):
        """Handle window close event."""
        self.db.disconnect()
        event.accept()

    def toggle_filters(self):
        """Toggle filter panel visibility."""
        is_visible = self.filter_panel.isVisible()
        self.filter_panel.setVisible(not is_visible)
    
        if self.filter_panel.isVisible():
            self.filter_toggle_btn.setText("Hide Filters")
        else:
            self.filter_toggle_btn.setText("Show Filters")

    def apply_filters(self):
        """Apply current filters to the collection."""
        name_query = self.search_input.text().strip()
        filters = self.filter_panel.get_filters()
    
        # Get filtered cards
        cards = self.db.filter_cards(name_query, filters)
    
        # Update current view
        if self.current_view == "table":
            self.populate_table(cards)
        else:
            self.gallery_view.set_cards(cards)
    
        self.statusBar().showMessage(f"Found {len(cards)} cards matching filters")

    def on_collection_table_hover(self, row, column):
        """Show card preview popup when hovering."""
        if row < 0 or row >= self.card_table.rowCount():
            self.card_preview_popup.hide_popup()
            return
    
        name_item = self.card_table.item(row, 0)
        if name_item:
            card = name_item.data(Qt.ItemDataRole.UserRole)
            if card:
                # Get global position from mouse cursor
                from PyQt5.QtGui import QCursor
                cursor_pos = QCursor.pos()
                self.card_preview_popup.show_card(card, cursor_pos)

    def eventFilter(self, obj, event):
        """Handle events to hide popup when leaving table."""
        if obj == self.card_table.viewport():
            if event.type() == event.Type.Leave:
                self.card_preview_popup.hide_popup()
        return super().eventFilter(obj, event)
