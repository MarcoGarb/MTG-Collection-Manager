"""
Dialog for selecting or creating decks.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt

from src.data.database import DatabaseManager
from src.models.deck import Deck
from src.ui.deck_builder_window import DeckBuilderWindow
from src.data.deck_importer import DeckImporter
from pathlib import Path

class DeckListDialog(QDialog):
    """Dialog for managing decks."""
    
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent_window = parent
        self.init_ui()
        self.load_decks()
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Deck Manager")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Table
        self.deck_table = QTableWidget()
        self.deck_table.setColumnCount(5)
        self.deck_table.setHorizontalHeaderLabels(["Name", "Format", "Colors", "Cards", "Modified"])
        self.deck_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.deck_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.deck_table.cellDoubleClicked.connect(lambda r, c: self.edit_deck())
        
        header = self.deck_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in [1, 2, 3, 4]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.deck_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        new_btn = QPushButton("New Deck")
        new_btn.clicked.connect(self.new_deck)
        button_layout.addWidget(new_btn)
        import_btn = QPushButton("Import Deck")
        import_btn.clicked.connect(self.import_deck)
        button_layout.addWidget(import_btn)
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self.edit_deck)
        button_layout.addWidget(edit_btn)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_deck)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def load_decks(self):
        """Load all decks."""
        decks = self.db.get_all_decks()
        self.deck_table.setRowCount(len(decks))
        
        for row, deck in enumerate(decks):
            self.deck_table.setItem(row, 0, QTableWidgetItem(deck.name))
            self.deck_table.setItem(row, 1, QTableWidgetItem(deck.format.capitalize()))
            self.deck_table.setItem(row, 2, QTableWidgetItem(deck.colors or "-"))
            
            # Get card count
            full_deck = self.db.get_deck(deck.id)
            card_count = full_deck.mainboard_count() if full_deck else 0
            self.deck_table.setItem(row, 3, QTableWidgetItem(str(card_count)))
            
            # Modified date
            modified = deck.date_modified.split('T')[0] if deck.date_modified else "-"
            self.deck_table.setItem(row, 4, QTableWidgetItem(modified))
            
            # Store deck ID in row
            self.deck_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, deck.id)
    
    def new_deck(self):
        """Create new deck."""
        builder = DeckBuilderWindow(self.db, parent=self.parent_window)
        builder.deck_saved.connect(self.on_deck_saved)
        builder.show()
        self.accept()
    
    def edit_deck(self):
        """Edit selected deck."""
        row = self.deck_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a deck to edit.")
            return
        
        deck_id = self.deck_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        deck = self.db.get_deck(deck_id)
        
        if deck:
            builder = DeckBuilderWindow(self.db, deck=deck, parent=self.parent_window)
            builder.deck_saved.connect(self.on_deck_saved)
            builder.show()
            self.accept()
    
    def delete_deck(self):
        """Delete selected deck."""
        row = self.deck_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a deck to delete.")
            return
        
        deck_name = self.deck_table.item(row, 0).text()
        reply = QMessageBox.question(
            self,
            "Delete Deck",
            f"Are you sure you want to delete '{deck_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deck_id = self.deck_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.db.delete_deck(deck_id)
            self.load_decks()
    
    def on_deck_saved(self, deck):
        """Handle deck saved."""
        self.load_decks()

    def import_deck(self):
        """Import deck from file."""
        from PyQt5.QtWidgets import QFileDialog, QInputDialog
    
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Deck",
            "",
            "Deck Files (*.txt *.csv);;Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
    
        if not file_path:
            return
    
        # Ask for deck name
        deck_name, ok = QInputDialog.getText(
            self,
            "Deck Name",
            "Enter deck name:",
            text=Path(file_path).stem
        )
    
        if not ok or not deck_name:
            return
    
        # Ask for format
        from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QDialogButtonBox, QLabel
    
        format_dialog = QDialog(self)
        format_dialog.setWindowTitle("Select Format")
        layout = QVBoxLayout()
    
        layout.addWidget(QLabel("Select deck format:"))
        format_combo = QComboBox()
        format_combo.addItems(['standard', 'commander', 'modern', 'pauper', 'legacy', 'vintage', 'brawl'])
        layout.addWidget(format_combo)
    
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(format_dialog.accept)
        buttons.rejected.connect(format_dialog.reject)
        layout.addWidget(buttons)
    
        format_dialog.setLayout(layout)
    
        if format_dialog.exec_() != QDialog.Accepted:
            return
    
        deck_format = format_combo.currentText()
    
        # Import deck
        try:
            importer = DeckImporter(self.db)
            deck, warnings = importer.import_deck(file_path, deck_name, deck_format)
        
            # Save to database
            deck_id = self.db.create_deck(deck)
            deck.id = deck_id
        
            # Show results
            message = f"Deck '{deck_name}' imported successfully!\n\n"
            message += f"Mainboard: {deck.mainboard_count()} cards\n"
            message += f"Sideboard: {deck.sideboard_count()} cards\n"
        
            if warnings:
                message += f"\n⚠ Warnings ({len(warnings)}):\n"
                message += "\n".join(warnings[:10])  # Show first 10 warnings
                if len(warnings) > 10:
                    message += f"\n... and {len(warnings) - 10} more"
        
            if importer.missing_cards:
                message += f"\n\n❌ Missing from collection ({len(importer.missing_cards)}):\n"
                message += "\n".join(importer.missing_cards[:10])
                if len(importer.missing_cards) > 10:
                    message += f"\n... and {len(importer.missing_cards) - 10} more"
        
            QMessageBox.information(self, "Import Complete", message)
            self.load_decks()
        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import deck:\n{str(e)}")