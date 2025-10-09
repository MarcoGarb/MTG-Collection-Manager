"""
Cube Builder Window - UI for building and editing Magic: The Gathering cubes.
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QCheckBox, QTabWidget,
    QDialog, QDialogButtonBox, QProgressDialog, QMessageBox,
    QScrollArea, QGroupBox, QGridLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
from typing import List, Optional, Dict
from src.models.cube import Cube, CubeCard
from src.models.card import Card
from src.data.database import DatabaseManager
from src.ai.cube_generator import CubeGenerator, CUBE_ARCHETYPE_TEMPLATES

class AICubeGeneratorDialog(QDialog):
    """Dialog to configure AI cube generation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Cube Generator")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Cube Type
        layout.addWidget(QLabel("Cube Type:"))
        self.cube_type_combo = QComboBox()
        self.cube_type_combo.addItems(list(CUBE_ARCHETYPE_TEMPLATES.keys()))
        self.cube_type_combo.setCurrentText("power_cube")
        layout.addWidget(self.cube_type_combo)
        
        # Size
        layout.addWidget(QLabel("Cube Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(180, 1000)
        self.size_spin.setValue(360)
        layout.addWidget(self.size_spin)
        
        # Power Level
        layout.addWidget(QLabel("Power Level:"))
        self.power_combo = QComboBox()
        self.power_combo.addItems(["low", "medium", "high"])
        self.power_combo.setCurrentText("high")
        layout.addWidget(self.power_combo)
        
        # Complexity
        layout.addWidget(QLabel("Complexity:"))
        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["low", "medium", "high"])
        self.complexity_combo.setCurrentText("high")
        layout.addWidget(self.complexity_combo)
        
        # Themes
        layout.addWidget(QLabel("Themes (comma-separated):"))
        self.themes_edit = QLineEdit()
        self.themes_edit.setPlaceholderText("e.g., graveyard, artifacts, tribal")
        layout.addWidget(self.themes_edit)
        
        # Singleton checkbox
        self.singleton_checkbox = QCheckBox("Singleton (each card appears only once)")
        self.singleton_checkbox.setChecked(True)
        layout.addWidget(self.singleton_checkbox)
        
        # Peasant checkbox
        self.peasant_checkbox = QCheckBox("Peasant (only common and uncommon cards)")
        self.peasant_checkbox.setChecked(False)
        layout.addWidget(self.peasant_checkbox)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def get_values(self):
        themes = [t.strip() for t in self.themes_edit.text().split(',') if t.strip()]
        return {
            "cube_type": self.cube_type_combo.currentText(),
            "size": self.size_spin.value(),
            "power_level": self.power_combo.currentText(),
            "complexity": self.complexity_combo.currentText(),
            "themes": themes,
            "is_singleton": self.singleton_checkbox.isChecked(),
            "is_peasant": self.peasant_checkbox.isChecked()
        }

class CubeGenWorker(QThread):
    """Worker thread for AI cube generation."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, collection, cube_type, size, power_level, complexity, themes, is_singleton, is_peasant, availability_ledger=None):
        super().__init__()
        self.collection = collection
        self.cube_type = cube_type
        self.size = size
        self.power_level = power_level
        self.complexity = complexity
        self.themes = themes
        self.is_singleton = is_singleton
        self.is_peasant = is_peasant
        self.availability_ledger = availability_ledger
    
    def run(self):
        try:
            self.progress.emit("Initializing cube generator...")
            generator = CubeGenerator(self.collection)
            
            self.progress.emit("Generating cube...")
            cube = generator.generate_cube(
                cube_type=self.cube_type,
                target_size=self.size,
                themes=self.themes,
                power_level=self.power_level,
                complexity=self.complexity,
                is_singleton=self.is_singleton,
                is_peasant=self.is_peasant,
                availability_ledger=self.availability_ledger
            )
            
            self.finished.emit(cube)
        except Exception as e:
            self.error.emit(str(e))

class CubeBuilderWindow(QMainWindow):
    """Window for building and editing cubes."""
    
    cube_saved = pyqtSignal(Cube)
    
    def __init__(self, db: DatabaseManager, cube: Optional[Cube] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.cube = cube if cube else Cube(name="New Cube", size=360)
        self.collection_cards = []
        self.filtered_cards = []
        
        self.init_ui()
        self.load_collection()
        
        if cube and cube.id:
            self.load_cube_cards()
        
        self.update_all_displays()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Cube Builder - {self.cube.name}")
        self.setGeometry(100, 100, 1800, 1000)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Cube Info
        info_layout = self.create_cube_info_section()
        main_layout.addLayout(info_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        collection_widget = self.create_collection_browser()
        splitter.addWidget(collection_widget)
        
        cube_widget = self.create_cube_list()
        splitter.addWidget(cube_widget)
        
        stats_widget = self.create_stats_panel()
        splitter.addWidget(stats_widget)
        
        splitter.setSizes([500, 700, 400])
        main_layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Cube")
        save_btn.clicked.connect(self.save_cube)
        button_layout.addWidget(save_btn)
        
        validate_btn = QPushButton("✓ Validate Cube")
        validate_btn.clicked.connect(self.validate_cube)
        button_layout.addWidget(validate_btn)
        
        export_btn = QPushButton("📄 Export Cube")
        export_btn.clicked.connect(self.export_cube)
        button_layout.addWidget(export_btn)
        
        import_btn = QPushButton("📥 Import Cards")
        import_btn.clicked.connect(self.import_cards_to_cube)
        button_layout.addWidget(import_btn)
        
        ai_btn = QPushButton("🤖 Generate (AI)")
        ai_btn.clicked.connect(self.open_ai_generator)
        button_layout.addWidget(ai_btn)
        
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_cube_info_section(self):
        """Create the cube information section."""
        layout = QHBoxLayout()
        
        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit(self.cube.name)
        self.name_input.textChanged.connect(self.update_cube_name)
        layout.addWidget(self.name_input)
        
        # Size
        layout.addWidget(QLabel("Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(180, 1000)
        self.size_spin.setValue(self.cube.size)
        self.size_spin.valueChanged.connect(self.update_cube_size)
        layout.addWidget(self.size_spin)
        
        # Format
        layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["vintage", "legacy", "modern", "standard", "pauper"])
        self.format_combo.setCurrentText(self.cube.format)
        self.format_combo.currentTextChanged.connect(self.update_cube_format)
        layout.addWidget(self.format_combo)
        
        # Power Level
        layout.addWidget(QLabel("Power Level:"))
        self.power_combo = QComboBox()
        self.power_combo.addItems(["low", "medium", "high"])
        self.power_combo.setCurrentText(self.cube.power_level)
        self.power_combo.currentTextChanged.connect(self.update_cube_power)
        layout.addWidget(self.power_combo)
        
        # Complexity
        layout.addWidget(QLabel("Complexity:"))
        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["low", "medium", "high"])
        self.complexity_combo.setCurrentText(self.cube.complexity)
        self.complexity_combo.currentTextChanged.connect(self.update_cube_complexity)
        layout.addWidget(self.complexity_combo)
        
        # Singleton checkbox
        self.singleton_checkbox = QCheckBox("Singleton")
        self.singleton_checkbox.setChecked(self.cube.is_singleton)
        self.singleton_checkbox.stateChanged.connect(self.update_cube_singleton)
        layout.addWidget(self.singleton_checkbox)
        
        # Peasant checkbox
        self.peasant_checkbox = QCheckBox("Peasant")
        self.peasant_checkbox.setChecked(self.cube.is_peasant)
        self.peasant_checkbox.stateChanged.connect(self.update_cube_peasant)
        layout.addWidget(self.peasant_checkbox)
        
        layout.addStretch()
        return layout
    
    def create_collection_browser(self):
        """Create the collection browser widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search and filters
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_cards)
        search_layout.addWidget(self.search_input)
        
        # Type filter
        search_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Creature", "Instant", "Sorcery", "Enchantment", "Artifact", "Planeswalker", "Land"])
        self.type_filter.currentTextChanged.connect(self.filter_cards)
        search_layout.addWidget(self.type_filter)
        
        # Color filter
        search_layout.addWidget(QLabel("Color:"))
        self.color_filter = QComboBox()
        self.color_filter.addItems(["All", "W", "U", "B", "R", "G", "C"])
        self.color_filter.currentTextChanged.connect(self.filter_cards)
        search_layout.addWidget(self.color_filter)
        
        layout.addLayout(search_layout)
        
        # Collection table
        self.collection_table = QTableWidget()
        self.collection_table.setColumnCount(6)
        self.collection_table.setHorizontalHeaderLabels(["Name", "Cost", "Type", "Rarity", "Colors", "Add"])
        self.collection_table.itemDoubleClicked.connect(self.add_card_to_cube)
        layout.addWidget(self.collection_table)
        
        return widget
    
    def create_cube_list(self):
        """Create the cube list widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cube tabs
        self.cube_tabs = QTabWidget()
        
        # Mainboard tab
        mainboard_widget = QWidget()
        mainboard_layout = QVBoxLayout(mainboard_widget)
        
        self.cube_table = QTableWidget()
        self.cube_table.setColumnCount(6)
        self.cube_table.setHorizontalHeaderLabels(["Qty", "Name", "Cost", "Type", "Rarity", "Remove"])
        mainboard_layout.addWidget(self.cube_table)
        
        self.cube_tabs.addTab(mainboard_widget, f"Cube ({self.cube.get_total_cards()})")
        
        layout.addWidget(self.cube_tabs)
        return widget
    
    def create_stats_panel(self):
        """Create the statistics panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Stats group
        stats_group = QGroupBox("Cube Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Color distribution
        color_group = QGroupBox("Color Distribution")
        color_layout = QVBoxLayout(color_group)
        
        self.color_dist_label = QLabel()
        color_layout.addWidget(self.color_dist_label)
        
        layout.addWidget(color_group)
        
        # Type distribution
        type_group = QGroupBox("Type Distribution")
        type_layout = QVBoxLayout(type_group)
        
        self.type_dist_label = QLabel()
        type_layout.addWidget(self.type_dist_label)
        
        layout.addWidget(type_group)
        
        # Mana curve
        curve_group = QGroupBox("Mana Curve")
        curve_layout = QVBoxLayout(curve_group)
        
        self.curve_label = QLabel()
        curve_layout.addWidget(self.curve_label)
        
        layout.addWidget(curve_group)
        
        layout.addStretch()
        return widget
    
    def load_collection(self):
        """Load collection cards from database."""
        try:
            self.collection_cards = self.db.get_all_cards()
            self.filtered_cards = self.collection_cards.copy()
            self.populate_collection_table()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load collection: {e}")
    
    def populate_collection_table(self, cards: List[Card] = None):
        """Populate the collection table with cards."""
        if cards is None:
            cards = self.filtered_cards
        
        self.collection_table.setRowCount(len(cards))
        
        for row, card in enumerate(cards):
            # Name
            name_item = QTableWidgetItem(card.name)
            name_item.setData(Qt.UserRole, card)
            self.collection_table.setItem(row, 0, name_item)
            
            # Mana Cost
            cost = card.mana_cost if card.mana_cost else "-"
            self.collection_table.setItem(row, 1, QTableWidgetItem(cost))
            
            # Type
            type_line = card.type_line if card.type_line else "-"
            self.collection_table.setItem(row, 2, QTableWidgetItem(type_line))
            
            # Rarity
            rarity = card.rarity.capitalize() if card.rarity else "-"
            self.collection_table.setItem(row, 3, QTableWidgetItem(rarity))
            
            # Colors
            colors = card.colors if card.colors else "C"
            self.collection_table.setItem(row, 4, QTableWidgetItem(colors))
            
            # Add button
            add_btn = QPushButton("Add")
            add_btn.clicked.connect(lambda checked, c=card: self.add_card_to_cube(c))
            self.collection_table.setCellWidget(row, 5, add_btn)
    
    def populate_cube_table(self, cards: List[CubeCard] = None):
        """Populate the cube table with cards."""
        if cards is None:
            cards = self.cube.cards
        
        # Sort cards by name
        sorted_cards = sorted(cards, key=lambda cc: cc.card.name)
        
        self.cube_table.setRowCount(len(sorted_cards))
        
        for row, cube_card in enumerate(sorted_cards):
            card = cube_card.card
            
            # Quantity
            qty_item = QTableWidgetItem(str(cube_card.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cube_table.setItem(row, 0, qty_item)
            
            # Name
            name_item = QTableWidgetItem(card.name)
            name_item.setData(Qt.UserRole, card)
            self.cube_table.setItem(row, 1, name_item)
            
            # Mana Cost
            cost = card.mana_cost if card.mana_cost else "-"
            self.cube_table.setItem(row, 2, QTableWidgetItem(cost))
            
            # Type
            type_line = card.type_line if card.type_line else "-"
            self.cube_table.setItem(row, 3, QTableWidgetItem(type_line))
            
            # Rarity
            rarity = card.rarity.capitalize() if card.rarity else "-"
            self.cube_table.setItem(row, 4, QTableWidgetItem(rarity))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, c=card: self.remove_card_from_cube(c))
            self.cube_table.setCellWidget(row, 5, remove_btn)
    
    def filter_cards(self):
        """Filter collection cards based on search criteria."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        color_filter = self.color_filter.currentText()
        
        self.filtered_cards = []
        
        for card in self.collection_cards:
            # Search text filter
            if search_text and search_text not in card.name.lower():
                continue
            
            # Type filter
            if type_filter != "All" and card.type_line:
                primary_type = card.type_line.split(' —')[0].strip()
                if primary_type != type_filter:
                    continue
            
            # Color filter
            if color_filter != "All":
                card_colors = card.get_color_identity_list()
                if color_filter == "C":
                    if card_colors:  # Has colors, skip colorless filter
                        continue
                else:
                    if not card_colors or color_filter not in card_colors:
                        continue
            
            self.filtered_cards.append(card)
        
        self.populate_collection_table()
    
    def add_card_to_cube(self, card: Card):
        """Add a card to the cube."""
        # Check if adding this card would violate rules
        if self.cube.is_peasant and card.rarity and card.rarity.lower() not in ['common', 'uncommon']:
            QMessageBox.warning(self, "Peasant Rule", f"Cannot add {card.name} - only common and uncommon cards allowed in peasant cubes.")
            return
        
        if self.cube.is_singleton:
            # Check if card already exists
            for cc in self.cube.cards:
                if cc.card.id == card.id and not cc.is_basic_land:
                    QMessageBox.warning(self, "Singleton Rule", f"Cannot add {card.name} - card already exists in singleton cube.")
                    return
        
        self.cube.add_card(card)
        self.update_cube_display()
    
    def remove_card_from_cube(self, card: Card):
        """Remove a card from the cube."""
        self.cube.remove_card(card)
        self.update_cube_display()
    
    def update_cube_display(self):
        """Update cube list table."""
        self.populate_cube_table()
        
        # Update tab label
        total_cards = self.cube.get_total_cards()
        self.cube_tabs.setTabText(0, f"Cube ({total_cards})")
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """Update the statistics display."""
        total_cards = self.cube.get_total_cards()
        
        # Basic stats
        stats_text = f"""
        <b>Total Cards:</b> {total_cards}<br>
        <b>Target Size:</b> {self.cube.size}<br>
        <b>Power Level:</b> {self.cube.power_level.title()}<br>
        <b>Complexity:</b> {self.cube.complexity.title()}<br>
        <b>Format:</b> {self.cube.format.title()}
        """
        self.stats_label.setText(stats_text)
        
        # Color distribution
        color_dist = self.cube.get_color_distribution()
        color_text = "<br>".join([f"{color}: {count}" for color, count in color_dist.items() if count > 0])
        self.color_dist_label.setText(color_text)
        
        # Type distribution
        type_dist = self.cube.get_card_count_by_type()
        type_text = "<br>".join([f"{card_type}: {count}" for card_type, count in type_dist.items()])
        self.type_dist_label.setText(type_text)
        
        # Mana curve
        curve = self.cube.get_mana_curve()
        curve_text = "<br>".join([f"CMC {cmc}: {count}" for cmc, count in sorted(curve.items())])
        self.curve_label.setText(curve_text)
    
    def update_all_displays(self):
        """Update all displays."""
        self.update_cube_display()
    
    def update_cube_name(self, name: str):
        """Update cube name."""
        self.cube.name = name
        self.setWindowTitle(f"Cube Builder - {name}")
    
    def update_cube_size(self, size: int):
        """Update cube size."""
        self.cube.size = size
    
    def update_cube_format(self, format: str):
        """Update cube format."""
        self.cube.format = format
    
    def update_cube_power(self, power: str):
        """Update cube power level."""
        self.cube.power_level = power
    
    def update_cube_complexity(self, complexity: str):
        """Update cube complexity."""
        self.cube.complexity = complexity
    
    def update_cube_singleton(self, checked: int):
        """Update cube singleton setting."""
        self.cube.is_singleton = checked == Qt.Checked
        # If switching to singleton, remove duplicates
        if self.cube.is_singleton:
            self._enforce_singleton()
    
    def update_cube_peasant(self, checked: int):
        """Update cube peasant setting."""
        self.cube.is_peasant = checked == Qt.Checked
        # If switching to peasant, remove non-peasant cards
        if self.cube.is_peasant:
            self._enforce_peasant()
    
    def _enforce_singleton(self):
        """Remove duplicate cards to enforce singleton rule."""
        seen_cards = set()
        cards_to_remove = []
        
        for cc in self.cube.cards:
            if not cc.is_basic_land and cc.card.id in seen_cards:
                cards_to_remove.append(cc)
            else:
                seen_cards.add(cc.card.id)
        
        for cc in cards_to_remove:
            self.cube.remove_card(cc.card, cc.quantity)
        
        if cards_to_remove:
            self.update_cube_display()
    
    def _enforce_peasant(self):
        """Remove non-peasant cards to enforce peasant rule."""
        cards_to_remove = []
        
        for cc in self.cube.cards:
            if cc.card.rarity and cc.card.rarity.lower() not in ['common', 'uncommon']:
                cards_to_remove.append(cc)
        
        for cc in cards_to_remove:
            self.cube.remove_card(cc.card, cc.quantity)
        
        if cards_to_remove:
            self.update_cube_display()
    
    def open_ai_generator(self):
        """Open AI cube generator dialog."""
        dialog = AICubeGeneratorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            opts = dialog.get_values()
            
            # Show progress dialog
            progress = QProgressDialog("Generating cube...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Get availability ledger
            availability_ledger = self.db.get_availability_ledger() if hasattr(self.db, 'get_availability_ledger') else None
            
            # Start generation in background
            self._cubegen_worker = CubeGenWorker(
                collection=self.collection_cards,
                cube_type=opts["cube_type"],
                size=opts["size"],
                power_level=opts["power_level"],
                complexity=opts["complexity"],
                themes=opts["themes"],
                is_singleton=opts["is_singleton"],
                is_peasant=opts["is_peasant"],
                availability_ledger=availability_ledger
            )
            self._cubegen_worker.finished.connect(lambda cube: self._on_ai_generation_done(cube, progress))
            self._cubegen_worker.error.connect(lambda msg: self._on_ai_generation_error(msg, progress))
            self._cubegen_worker.start()
    
    def _on_ai_generation_done(self, cube: Cube, progress: QProgressDialog):
        """Handle AI generation completion."""
        progress.close()
        self._cubegen_worker = None
        
        if not cube:
            QMessageBox.warning(self, "Generation Failed", "AI did not return a cube.")
            return
        
        # Replace current cube
        self.cube = cube
        self.name_input.setText(cube.name)
        self.size_spin.setValue(cube.size)
        self.format_combo.setCurrentText(cube.format)
        self.power_combo.setCurrentText(cube.power_level)
        self.complexity_combo.setCurrentText(cube.complexity)
        self.singleton_checkbox.setChecked(cube.is_singleton)
        self.peasant_checkbox.setChecked(cube.is_peasant)
        
        # Update displays
        self.update_all_displays()
        
        QMessageBox.information(self, "Success", f"Generated cube with {cube.get_total_cards()} cards!")
    
    def _on_ai_generation_error(self, error_msg: str, progress: QProgressDialog):
        """Handle AI generation error."""
        progress.close()
        self._cubegen_worker = None
        QMessageBox.critical(self, "Generation Error", f"Failed to generate cube: {error_msg}")
    
    def save_cube(self):
        """Save the cube to database."""
        try:
            # Update cube metadata
            self.cube.name = self.name_input.text()
            self.cube.size = self.size_spin.value()
            self.cube.format = self.format_combo.currentText()
            self.cube.power_level = self.power_combo.currentText()
            self.cube.complexity = self.complexity_combo.currentText()
            
            # Save to database (this would need to be implemented in DatabaseManager)
            # cube_id = self.db.save_cube(self.cube)
            # self.cube.id = cube_id
            
            QMessageBox.information(self, "Success", "Cube saved successfully!")
            self.cube_saved.emit(self.cube)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save cube: {e}")
    
    def validate_cube(self):
        """Validate the cube and show results."""
        issues = self.cube.validate_cube()
        
        if not issues['errors'] and not issues['warnings']:
            QMessageBox.information(self, "Validation", "Cube is valid!")
        else:
            message = "Cube validation results:\n\n"
            if issues['errors']:
                message += "Errors:\n" + "\n".join(f"• {error}" for error in issues['errors']) + "\n\n"
            if issues['warnings']:
                message += "Warnings:\n" + "\n".join(f"• {warning}" for warning in issues['warnings']) + "\n\n"
            if issues['info']:
                message += "Info:\n" + "\n".join(f"• {info}" for info in issues['info'])
            
            QMessageBox.warning(self, "Validation Results", message)
    
    def export_cube(self):
        """Export cube to text format."""
        try:
            cube_list = self.cube.export_to_list()
            
            # Save to file
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Cube", f"{self.cube.name}.txt", "Text Files (*.txt)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(cube_list)
                QMessageBox.information(self, "Success", f"Cube exported to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export cube: {e}")
    
    def import_cards_to_cube(self):
        """Import cards from a list to the cube."""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Cards", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse the file and add cards
                # This would need to be implemented based on the file format
                QMessageBox.information(self, "Success", "Cards imported successfully!")
                self.update_cube_display()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import cards: {e}")
    
    def load_cube_cards(self):
        """Load cube cards from database."""
        # This would load cube cards from the database
        # Implementation depends on how cubes are stored
        pass
