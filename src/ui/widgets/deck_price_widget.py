"""
Widget displaying deck price statistics and breakdown.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from typing import List

from src.models.deck import Deck, DeckCard


class DeckPriceWidget(QWidget):
    """Widget showing deck price breakdown and statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("💰 Price Analysis")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Summary stats
        summary_group = QGroupBox("Price Summary")
        summary_layout = QVBoxLayout()
        
        self.total_value_label = QLabel("Total Value: $0.00")
        self.total_value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.total_value_label)
        
        self.mainboard_value_label = QLabel("Mainboard: $0.00")
        summary_layout.addWidget(self.mainboard_value_label)
        
        self.sideboard_value_label = QLabel("Sideboard: $0.00")
        summary_layout.addWidget(self.sideboard_value_label)
        
        self.avg_card_price_label = QLabel("Avg per Card: $0.00")
        summary_layout.addWidget(self.avg_card_price_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Price by type
        type_group = QGroupBox("Value by Type")
        type_layout = QVBoxLayout()
        
        self.creatures_value_label = QLabel("Creatures: $0.00")
        type_layout.addWidget(self.creatures_value_label)
        
        self.lands_value_label = QLabel("Lands: $0.00")
        type_layout.addWidget(self.lands_value_label)
        
        self.spells_value_label = QLabel("Spells: $0.00")
        type_layout.addWidget(self.spells_value_label)
        
        self.other_value_label = QLabel("Other: $0.00")
        type_layout.addWidget(self.other_value_label)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Most expensive cards table
        expensive_group = QGroupBox("Most Expensive Cards")
        expensive_layout = QVBoxLayout()
        
        self.expensive_table = QTableWidget()
        self.expensive_table.setColumnCount(3)
        self.expensive_table.setHorizontalHeaderLabels(["Card", "Qty", "Value"])
        self.expensive_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.expensive_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.expensive_table.setMaximumHeight(200)
        
        header = self.expensive_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        expensive_layout.addWidget(self.expensive_table)
        expensive_group.setLayout(expensive_layout)
        layout.addWidget(expensive_group)
        
        layout.addStretch()
    
    def set_deck(self, deck: Deck):
        """Update widget with deck data."""
        self.deck = deck
        self.update_display()
    
    def update_display(self):
        """Update all price displays."""
        if not self.deck:
            return
        
        mainboard = self.deck.get_mainboard_cards()
        sideboard = self.deck.get_sideboard_cards()
        
        # Calculate total values
        mainboard_value = sum(
            (dc.card.current_price or 0) * dc.quantity 
            for dc in mainboard
        )
        
        sideboard_value = sum(
            (dc.card.current_price or 0) * dc.quantity 
            for dc in sideboard
        )
        
        total_value = mainboard_value + sideboard_value
        
        # Update summary
        self.total_value_label.setText(f"Total Value: ${total_value:.2f}")
        self.mainboard_value_label.setText(f"Mainboard: ${mainboard_value:.2f}")
        self.sideboard_value_label.setText(f"Sideboard: ${sideboard_value:.2f}")
        
        # Average per card
        total_cards = self.deck.total_cards()
        avg_price = total_value / total_cards if total_cards > 0 else 0
        self.avg_card_price_label.setText(f"Avg per Card: ${avg_price:.2f}")
        
        # Calculate by type
        creatures_value = sum(
            (dc.card.current_price or 0) * dc.quantity 
            for dc in mainboard 
            if dc.card.is_creature()
        )
        
        lands_value = sum(
            (dc.card.current_price or 0) * dc.quantity 
            for dc in mainboard 
            if dc.card.is_land()
        )
        
        spells_value = sum(
            (dc.card.current_price or 0) * dc.quantity 
            for dc in mainboard 
            if dc.card.is_instant_or_sorcery()
        )
        
        other_value = mainboard_value - (creatures_value + lands_value + spells_value)
        
        self.creatures_value_label.setText(f"Creatures: ${creatures_value:.2f}")
        self.lands_value_label.setText(f"Lands: ${lands_value:.2f}")
        self.spells_value_label.setText(f"Spells: ${spells_value:.2f}")
        self.other_value_label.setText(f"Other: ${other_value:.2f}")
        
        # Most expensive cards
        all_cards = mainboard + sideboard
        # Sort by total value (price * quantity)
        sorted_cards = sorted(
            all_cards,
            key=lambda dc: (dc.card.current_price or 0) * dc.quantity,
            reverse=True
        )
        
        # Show top 10
        top_cards = sorted_cards[:10]
        self.expensive_table.setRowCount(len(top_cards))
        
        for row, dc in enumerate(top_cards):
            card_price = dc.card.current_price or 0
            total_card_value = card_price * dc.quantity
            
            # Card name
            name_item = QTableWidgetItem(dc.card.name)
            if dc.in_sideboard:
                name_item.setForeground(QColor('#888888'))
            self.expensive_table.setItem(row, 0, name_item)
            
            # Quantity
            qty_item = QTableWidgetItem(str(dc.quantity))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.expensive_table.setItem(row, 1, qty_item)
            
            # Value
            value_item = QTableWidgetItem(f"${total_card_value:.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            
            # Color code by price
            if total_card_value >= 20:
                value_item.setForeground(QColor('#ff0000'))  # Red for expensive
            elif total_card_value >= 10:
                value_item.setForeground(QColor('#ff8800'))  # Orange
            elif total_card_value >= 5:
                value_item.setForeground(QColor('#ffaa00'))  # Yellow
            
            self.expensive_table.setItem(row, 2, value_item)