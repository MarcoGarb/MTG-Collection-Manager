"""
Widget displaying card recommendations for deck building.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QScrollArea, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from src.models.deck import Deck
from src.models.card import Card
from src.ai.card_recommender import CardRecommender  # UPDATED IMPORT
from typing import List


class DeckRecommendationsWidget(QWidget):
    """Widget showing card recommendations for deck improvement."""
    
    card_selected = pyqtSignal(Card)  # Emit when user wants to add a card
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = None
        self.collection = []
        self.recommender = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("💡 Recommendations")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_recommendations)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Tabs for different recommendation categories
        self.tabs = QTabWidget()
        
        # Synergy tab
        self.synergy_table = self._create_recommendation_table()
        self.tabs.addTab(self.synergy_table, "⚡ Synergy")
        
        # Curve fillers tab
        self.curve_table = self._create_recommendation_table()
        self.tabs.addTab(self.curve_table, "📊 Curve")
        
        # Removal tab
        self.removal_table = self._create_recommendation_table()
        self.tabs.addTab(self.removal_table, "💥 Removal")
        
        # Card draw tab
        self.draw_table = self._create_recommendation_table()
        self.tabs.addTab(self.draw_table, "📖 Draw")
        
        # Ramp tab
        self.ramp_table = self._create_recommendation_table()
        self.tabs.addTab(self.ramp_table, "🌱 Ramp")
        
        # Lands tab
        self.lands_table = self._create_recommendation_table()
        self.tabs.addTab(self.lands_table, "🏔️ Lands")
        
        # Staples tab
        self.staples_table = self._create_recommendation_table()
        self.tabs.addTab(self.staples_table, "⭐ Staples")
        
        layout.addWidget(self.tabs)
        
        # Info label
        self.info_label = QLabel("Add cards to your deck to get recommendations")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)
    
    def _create_recommendation_table(self) -> QTableWidget:
        """Create a table for recommendations."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Card", "Cost", "Type", "Reason", ""])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        return table
    
    def set_deck_and_collection(self, deck: Deck, collection: List[Card]):
        """Update widget with deck and collection data."""
        self.deck = deck
        self.collection = collection
        self.refresh_recommendations()
    
    def refresh_recommendations(self):
        """Refresh all recommendations."""
        if not self.deck or not self.collection:
            return
        
        self.info_label.setText("Analyzing deck...")
        
        # Create recommender
        self.recommender = CardRecommender(self.deck, self.collection)
        
        # Get recommendations
        recommendations = self.recommender.get_recommendations(max_recommendations=15)
        
        # Populate tables
        self._populate_table(self.synergy_table, recommendations['synergy'])
        self._populate_table(self.curve_table, recommendations['curve'])
        self._populate_table(self.removal_table, recommendations['removal'])
        self._populate_table(self.draw_table, recommendations['draw'])
        self._populate_table(self.ramp_table, recommendations['ramp'])
        self._populate_table(self.lands_table, recommendations['lands'])
        self._populate_table(self.staples_table, recommendations['staples'])
        
        # Update tab labels with counts
        self.tabs.setTabText(0, f"⚡ Synergy ({len(recommendations['synergy'])})")
        self.tabs.setTabText(1, f"📊 Curve ({len(recommendations['curve'])})")
        self.tabs.setTabText(2, f"💥 Removal ({len(recommendations['removal'])})")
        self.tabs.setTabText(3, f"📖 Draw ({len(recommendations['draw'])})")
        self.tabs.setTabText(4, f"🌱 Ramp ({len(recommendations['ramp'])})")
        self.tabs.setTabText(5, f"🏔️ Lands ({len(recommendations['lands'])})")
        self.tabs.setTabText(6, f"⭐ Staples ({len(recommendations['staples'])})")
        
        total = sum(len(recs) for recs in recommendations.values())
        self.info_label.setText(f"Found {total} recommendations from your collection")
    
    def _populate_table(self, table: QTableWidget, recommendations):
        """Populate a recommendation table."""
        table.setRowCount(len(recommendations))
        
        for row, (card, reason, score) in enumerate(recommendations):
            # Card name
            name_item = QTableWidgetItem(card.name)
            name_item.setData(Qt.ItemDataRole.UserRole, card)  # Store card object
            
            # Color by score
            if score >= 8:
                name_item.setForeground(QColor('#00aa00'))  # Green for high score
            elif score >= 6:
                name_item.setForeground(QColor('#0088ff'))  # Blue for medium
            
            table.setItem(row, 0, name_item)
            
            # Mana cost
            cost = card.mana_cost if card.mana_cost else "-"
            table.setItem(row, 1, QTableWidgetItem(cost))
            
            # Type
            type_line = card.type_line if card.type_line else "-"
            table.setItem(row, 2, QTableWidgetItem(type_line))
            
            # Reason
            table.setItem(row, 3, QTableWidgetItem(reason))
            
            # Add button
            add_btn = QPushButton("Add →")
            add_btn.clicked.connect(lambda checked, c=card: self.card_selected.emit(c))
            table.setCellWidget(row, 4, add_btn)