"""
Advanced filter panel for collection filtering.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QLineEdit, QPushButton, QGroupBox, QGridLayout,
    QScrollArea, QDoubleSpinBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, List, Optional


class FilterPanel(QWidget):
    """Panel for filtering cards by various criteria."""
    
    filters_changed = pyqtSignal()  # Emitted when filters change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Title
        title = QLabel("Filters")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title)
        
        # Scroll area for filters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumWidth(300)
        
        container = QWidget()
        filters_layout = QVBoxLayout()
        container.setLayout(filters_layout)
        
        # === RARITY FILTER ===
        rarity_group = QGroupBox("Rarity")
        rarity_layout = QVBoxLayout()
        
        self.rarity_common = QCheckBox("Common")
        self.rarity_common.setChecked(True)
        self.rarity_common.stateChanged.connect(self.filters_changed.emit)
        rarity_layout.addWidget(self.rarity_common)
        
        self.rarity_uncommon = QCheckBox("Uncommon")
        self.rarity_uncommon.setChecked(True)
        self.rarity_uncommon.stateChanged.connect(self.filters_changed.emit)
        rarity_layout.addWidget(self.rarity_uncommon)
        
        self.rarity_rare = QCheckBox("Rare")
        self.rarity_rare.setChecked(True)
        self.rarity_rare.stateChanged.connect(self.filters_changed.emit)
        rarity_layout.addWidget(self.rarity_rare)
        
        self.rarity_mythic = QCheckBox("Mythic")
        self.rarity_mythic.setChecked(True)
        self.rarity_mythic.stateChanged.connect(self.filters_changed.emit)
        rarity_layout.addWidget(self.rarity_mythic)
        
        rarity_group.setLayout(rarity_layout)
        filters_layout.addWidget(rarity_group)
        
        # === FOIL FILTER ===
        foil_group = QGroupBox("Foil")
        foil_layout = QVBoxLayout()
        
        self.foil_combo = QComboBox()
        self.foil_combo.addItems(["All", "Foil Only", "Non-Foil Only"])
        self.foil_combo.currentIndexChanged.connect(self.filters_changed.emit)
        foil_layout.addWidget(self.foil_combo)
        
        foil_group.setLayout(foil_layout)
        filters_layout.addWidget(foil_group)
        
        # === CONDITION FILTER ===
        condition_group = QGroupBox("Condition")
        condition_layout = QVBoxLayout()
        
        self.condition_combo = QComboBox()
        self.condition_combo.addItems([
            "All",
            "Near Mint",
            "Lightly Played",
            "Moderately Played",
            "Heavily Played",
            "Damaged"
        ])
        self.condition_combo.currentIndexChanged.connect(self.filters_changed.emit)
        condition_layout.addWidget(self.condition_combo)
        
        condition_group.setLayout(condition_layout)
        filters_layout.addWidget(condition_group)
        
        # === PRICE FILTER ===
        price_group = QGroupBox("Price Range")
        price_layout = QGridLayout()
        
        price_layout.addWidget(QLabel("Min:"), 0, 0)
        self.price_min = QDoubleSpinBox()
        self.price_min.setPrefix("$")
        self.price_min.setRange(0, 10000)
        self.price_min.setValue(0)
        self.price_min.setSingleStep(0.50)
        self.price_min.valueChanged.connect(self.filters_changed.emit)
        price_layout.addWidget(self.price_min, 0, 1)
        
        price_layout.addWidget(QLabel("Max:"), 1, 0)
        self.price_max = QDoubleSpinBox()
        self.price_max.setPrefix("$")
        self.price_max.setRange(0, 10000)
        self.price_max.setValue(10000)
        self.price_max.setSingleStep(0.50)
        self.price_max.valueChanged.connect(self.filters_changed.emit)
        price_layout.addWidget(self.price_max, 1, 1)
        
        self.price_only_priced = QCheckBox("Only cards with prices")
        self.price_only_priced.stateChanged.connect(self.filters_changed.emit)
        price_layout.addWidget(self.price_only_priced, 2, 0, 1, 2)
        
        price_group.setLayout(price_layout)
        filters_layout.addWidget(price_group)
        
        # === SET FILTER ===
        set_group = QGroupBox("Set")
        set_layout = QVBoxLayout()
        
        self.set_input = QLineEdit()
        self.set_input.setPlaceholderText("Enter set code (e.g., NEO)")
        self.set_input.textChanged.connect(self.filters_changed.emit)
        set_layout.addWidget(self.set_input)
        
        set_group.setLayout(set_layout)
        filters_layout.addWidget(set_group)
        
        # === LANGUAGE FILTER ===
        language_group = QGroupBox("Language")
        language_layout = QVBoxLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "All",
            "English (en)",
            "Spanish (es)",
            "French (fr)",
            "German (de)",
            "Italian (it)",
            "Portuguese (pt)",
            "Japanese (ja)",
            "Korean (ko)",
            "Russian (ru)",
            "Chinese Simplified (zhs)",
            "Chinese Traditional (zht)"
        ])
        self.language_combo.currentIndexChanged.connect(self.filters_changed.emit)
        language_layout.addWidget(self.language_combo)
        
        language_group.setLayout(language_layout)
        filters_layout.addWidget(language_group)
        
                # === COLORS FILTER ===
        colors_group = QGroupBox("Colors")
        colors_layout = QVBoxLayout()

        # Color checkboxes
        color_checks_layout = QHBoxLayout()
        self.color_white = QCheckBox("W")
        self.color_white.stateChanged.connect(self.filters_changed.emit)
        color_checks_layout.addWidget(self.color_white)

        self.color_blue = QCheckBox("U")
        self.color_blue.stateChanged.connect(self.filters_changed.emit)
        color_checks_layout.addWidget(self.color_blue)

        self.color_black = QCheckBox("B")
        self.color_black.stateChanged.connect(self.filters_changed.emit)
        color_checks_layout.addWidget(self.color_black)

        self.color_red = QCheckBox("R")
        self.color_red.stateChanged.connect(self.filters_changed.emit)
        color_checks_layout.addWidget(self.color_red)

        self.color_green = QCheckBox("G")
        self.color_green.stateChanged.connect(self.filters_changed.emit)
        color_checks_layout.addWidget(self.color_green)

        colors_layout.addLayout(color_checks_layout)

        # Colorless checkbox
        self.color_colorless = QCheckBox("Colorless")
        self.color_colorless.stateChanged.connect(self.filters_changed.emit)
        colors_layout.addWidget(self.color_colorless)

        # Color mode
        self.color_mode = QComboBox()
        self.color_mode.addItems(["At least these colors", "Exactly these colors", "Exclude these colors"])
        self.color_mode.currentIndexChanged.connect(self.filters_changed.emit)
        colors_layout.addWidget(self.color_mode)

        colors_group.setLayout(colors_layout)
        filters_layout.addWidget(colors_group)

        # === MANA COST (CMC) FILTER ===
        cmc_group = QGroupBox("Mana Cost (CMC)")
        cmc_layout = QGridLayout()

        cmc_layout.addWidget(QLabel("Min:"), 0, 0)
        self.cmc_min = QDoubleSpinBox()
        self.cmc_min.setDecimals(0)
        self.cmc_min.setRange(0, 20)
        self.cmc_min.setValue(0)
        self.cmc_min.valueChanged.connect(self.filters_changed.emit)
        cmc_layout.addWidget(self.cmc_min, 0, 1)

        cmc_layout.addWidget(QLabel("Max:"), 1, 0)
        self.cmc_max = QDoubleSpinBox()
        self.cmc_max.setDecimals(0)
        self.cmc_max.setRange(0, 20)
        self.cmc_max.setValue(20)
        self.cmc_max.valueChanged.connect(self.filters_changed.emit)
        cmc_layout.addWidget(self.cmc_max, 1, 1)

        cmc_group.setLayout(cmc_layout)
        filters_layout.addWidget(cmc_group)

        # === CARD TYPES FILTER ===
        types_group = QGroupBox("Card Types")
        types_layout = QVBoxLayout()

        self.type_creature = QCheckBox("Creature")
        self.type_creature.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_creature)

        self.type_instant = QCheckBox("Instant")
        self.type_instant.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_instant)

        self.type_sorcery = QCheckBox("Sorcery")
        self.type_sorcery.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_sorcery)

        self.type_enchantment = QCheckBox("Enchantment")
        self.type_enchantment.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_enchantment)

        self.type_artifact = QCheckBox("Artifact")
        self.type_artifact.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_artifact)

        self.type_planeswalker = QCheckBox("Planeswalker")
        self.type_planeswalker.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_planeswalker)

        self.type_land = QCheckBox("Land")
        self.type_land.stateChanged.connect(self.filters_changed.emit)
        types_layout.addWidget(self.type_land)

        types_group.setLayout(types_layout)
        filters_layout.addWidget(types_group)

        # === QUANTITY FILTER ===
        quantity_group = QGroupBox("Quantity")
        quantity_layout = QGridLayout()
        
        quantity_layout.addWidget(QLabel("Min:"), 0, 0)
        self.quantity_min = QDoubleSpinBox()
        self.quantity_min.setDecimals(0)
        self.quantity_min.setRange(0, 1000)
        self.quantity_min.setValue(1)
        self.quantity_min.valueChanged.connect(self.filters_changed.emit)
        quantity_layout.addWidget(self.quantity_min, 0, 1)
        
        quantity_layout.addWidget(QLabel("Max:"), 1, 0)
        self.quantity_max = QDoubleSpinBox()
        self.quantity_max.setDecimals(0)
        self.quantity_max.setRange(1, 1000)
        self.quantity_max.setValue(1000)
        self.quantity_max.valueChanged.connect(self.filters_changed.emit)
        quantity_layout.addWidget(self.quantity_max, 1, 1)
        
        quantity_group.setLayout(quantity_layout)
        filters_layout.addWidget(quantity_group)
        
        filters_layout.addStretch()
        
        # === CONTROL BUTTONS ===
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self.reset_filters)
        buttons_layout.addWidget(reset_btn)
        
        filters_layout.addLayout(buttons_layout)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
    def get_filters(self) -> Dict:
        """Get current filter values as dictionary."""
        filters = {}
        
        # Rarity filter
        rarities = []
        if self.rarity_common.isChecked():
            rarities.append('common')
        if self.rarity_uncommon.isChecked():
            rarities.append('uncommon')
        if self.rarity_rare.isChecked():
            rarities.append('rare')
        if self.rarity_mythic.isChecked():
            rarities.append('mythic')
        filters['rarities'] = rarities
        
        # Foil filter
        foil_text = self.foil_combo.currentText()
        if foil_text == "Foil Only":
            filters['foil'] = True
        elif foil_text == "Non-Foil Only":
            filters['foil'] = False
        else:
            filters['foil'] = None
            
        # Condition filter
        condition_text = self.condition_combo.currentText()
        if condition_text != "All":
            filters['condition'] = condition_text.lower().replace(' ', '_')
        else:
            filters['condition'] = None
            
        # Price filter
        filters['price_min'] = self.price_min.value()
        filters['price_max'] = self.price_max.value()
        filters['only_priced'] = self.price_only_priced.isChecked()
        
        # Set filter
        set_code = self.set_input.text().strip()
        if set_code:
            filters['set_code'] = set_code.upper()
        else:
            filters['set_code'] = None
            
        # Language filter
        language_text = self.language_combo.currentText()
        if language_text != "All":
            # Extract language code from "English (en)" format
            lang_code = language_text.split('(')[1].rstrip(')')
            filters['language'] = lang_code
        else:
            filters['language'] = None
            
                # Colors filter
        selected_colors = []
        if self.color_white.isChecked():
            selected_colors.append('W')
        if self.color_blue.isChecked():
            selected_colors.append('U')
        if self.color_black.isChecked():
            selected_colors.append('B')
        if self.color_red.isChecked():
            selected_colors.append('R')
        if self.color_green.isChecked():
            selected_colors.append('G')

        if selected_colors:
            filters['colors'] = selected_colors
            color_mode_text = self.color_mode.currentText()
            if "Exactly" in color_mode_text:
                filters['color_mode'] = 'exact'
            elif "Exclude" in color_mode_text:
                filters['color_mode'] = 'exclude'
            else:
                filters['color_mode'] = 'include'
        else:
            filters['colors'] = None
    
        filters['colorless'] = self.color_colorless.isChecked()

        # CMC filter
        filters['cmc_min'] = self.cmc_min.value() if self.cmc_min.value() > 0 else None
        filters['cmc_max'] = self.cmc_max.value() if self.cmc_max.value() < 20 else None

        # Card types filter
        selected_types = []
        if self.type_creature.isChecked():
            selected_types.append('Creature')
        if self.type_instant.isChecked():
            selected_types.append('Instant')
        if self.type_sorcery.isChecked():
            selected_types.append('Sorcery')
        if self.type_enchantment.isChecked():
            selected_types.append('Enchantment')
        if self.type_artifact.isChecked():
            selected_types.append('Artifact')
        if self.type_planeswalker.isChecked():
            selected_types.append('Planeswalker')
        if self.type_land.isChecked():
            selected_types.append('Land')

        filters['card_types'] = selected_types if selected_types else None

        # Quantity filter
        filters['quantity_min'] = int(self.quantity_min.value())
        filters['quantity_max'] = int(self.quantity_max.value())
        
        return filters
        
    def reset_filters(self):
        """Reset all filters to default values."""
        # Rarity
        self.rarity_common.setChecked(True)
        self.rarity_uncommon.setChecked(True)
        self.rarity_rare.setChecked(True)
        self.rarity_mythic.setChecked(True)
        
        # Foil
        self.foil_combo.setCurrentIndex(0)
        
        # Condition
        self.condition_combo.setCurrentIndex(0)
        
        # Price
        self.price_min.setValue(0)
        self.price_max.setValue(10000)
        self.price_only_priced.setChecked(False)
        
        # Set
        self.set_input.clear()
        
        # Language
        self.language_combo.setCurrentIndex(0)
        
        # Colors
        self.color_white.setChecked(False)
        self.color_blue.setChecked(False)
        self.color_black.setChecked(False)
        self.color_red.setChecked(False)
        self.color_green.setChecked(False)
        self.color_colorless.setChecked(False)
        self.color_mode.setCurrentIndex(0)

        # CMC
        self.cmc_min.setValue(0)
        self.cmc_max.setValue(20)

        # Types
        self.type_creature.setChecked(False)
        self.type_instant.setChecked(False)
        self.type_sorcery.setChecked(False)
        self.type_enchantment.setChecked(False)
        self.type_artifact.setChecked(False)
        self.type_planeswalker.setChecked(False)
        self.type_land.setChecked(False)

        # Quantity
        self.quantity_min.setValue(1)
        self.quantity_max.setValue(1000)
        
        self.filters_changed.emit()
