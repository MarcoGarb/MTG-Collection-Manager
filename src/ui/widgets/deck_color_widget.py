""" Widget displaying deck color distribution and mana analysis. """
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import re

from src.models.deck import Deck

class DeckColorWidget(QWidget):
    """Widget showing deck color distribution and mana analysis."""
    
    # MTG color mapping
    COLOR_NAMES = {
        'W': 'White',
        'U': 'Blue',
        'B': 'Black',
        'R': 'Red',
        'G': 'Green',
        'C': 'Colorless'
    }
    
    COLOR_HEX = {
        'W': '#F9FAF4',
        'U': '#0E68AB',
        'B': '#150B00',
        'R': '#D3202A',
        'G': '#00733E',
        'C': '#CAC5C0'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        
        # Header
        header = QLabel("🎨 Color Analysis")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Color Identity Summary
        identity_group = QGroupBox("Color Identity")
        identity_layout = QVBoxLayout()
        self.identity_label = QLabel("Colors: -")
        self.identity_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        identity_layout.addWidget(self.identity_label)
        identity_group.setLayout(identity_layout)
        layout.addWidget(identity_group)
        
        # Color Pie Chart
        self.pie_figure = Figure(figsize=(5, 4))
        self.pie_canvas = FigureCanvasQTAgg(self.pie_figure)
        layout.addWidget(QLabel("Card Distribution by Color"))
        layout.addWidget(self.pie_canvas)
        
        # Mana Symbol Breakdown
        mana_group = QGroupBox("Mana Symbol Analysis")
        self.mana_layout = QVBoxLayout()
        mana_group.setLayout(self.mana_layout)
        layout.addWidget(mana_group)
        
        # Devotion
        devotion_group = QGroupBox("Devotion (Mana Symbols in Costs)")
        self.devotion_layout = QVBoxLayout()
        devotion_group.setLayout(self.devotion_layout)
        layout.addWidget(devotion_group)
        
        # Pip Distribution Chart
        self.pip_figure = Figure(figsize=(5, 3))
        self.pip_canvas = FigureCanvasQTAgg(self.pip_figure)
        layout.addWidget(QLabel("Colored Mana Symbols Distribution"))
        layout.addWidget(self.pip_canvas)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def set_deck(self, deck: Deck):
        """Update widget with deck data."""
        self.deck = deck
        self.update_display()
    
    def update_display(self):
        """Update all color displays."""
        if not self.deck:
            return
        
        mainboard = self.deck.get_mainboard_cards()
        
        # Update color identity
        colors = self.deck.get_colors()
        if colors:
            color_names = [self.COLOR_NAMES.get(c, c) for c in colors]
            self.identity_label.setText(f"Colors: {', '.join(color_names)}")
        else:
            self.identity_label.setText("Colors: Colorless")
        
        # Calculate color distribution
        color_distribution = self._calculate_color_distribution(mainboard)
        self._update_color_pie_chart(color_distribution)
        
        # Calculate mana symbol breakdown
        mana_symbols = self._calculate_mana_symbols(mainboard)
        self._update_mana_breakdown(mana_symbols)
        
        # Calculate devotion
        devotion = self._calculate_devotion(mainboard)
        self._update_devotion_display(devotion)
        
        # Update pip distribution chart
        self._update_pip_chart(mana_symbols)
    
    def _calculate_color_distribution(self, cards):
        """Calculate how many cards of each color."""
        distribution = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0,
            'Colorless': 0, 'Multicolor': 0
        }
        
        for dc in cards:
            colors = dc.card.get_colors_list()
            
            if len(colors) == 0:
                distribution['Colorless'] += dc.quantity
            elif len(colors) == 1:
                distribution[colors[0]] += dc.quantity
            else:
                distribution['Multicolor'] += dc.quantity
        
        return distribution
    
    def _calculate_mana_symbols(self, cards):
        """Count mana symbols in all mana costs."""
        symbols = {
            'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0,
            'Generic': 0, 'Hybrid': 0, 'Phyrexian': 0
        }
        
        for dc in cards:
            if not dc.card.mana_cost:
                continue
            
            cost = dc.card.mana_cost
            quantity = dc.quantity
            
            # Count each symbol type
            symbols['W'] += cost.count('{W}') * quantity
            symbols['U'] += cost.count('{U}') * quantity
            symbols['B'] += cost.count('{B}') * quantity
            symbols['R'] += cost.count('{R}') * quantity
            symbols['G'] += cost.count('{G}') * quantity
            symbols['C'] += cost.count('{C}') * quantity
            
            # Count generic mana (numbers)
            generic_matches = re.findall(r'\{(\d+)\}', cost)
            for match in generic_matches:
                symbols['Generic'] += int(match) * quantity
            
            # Count hybrid/phyrexian (simplified)
            if '/' in cost:
                if 'P' in cost:
                    symbols['Phyrexian'] += cost.count('/') * quantity
                else:
                    symbols['Hybrid'] += cost.count('/') * quantity
        
        return symbols
    
    def _calculate_devotion(self, cards):
        """Calculate devotion (colored mana symbols) for each color."""
        devotion = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0}
        
        for dc in cards:
            if not dc.card.mana_cost:
                continue
            
            cost = dc.card.mana_cost
            quantity = dc.quantity
            
            # Count colored symbols (including hybrid)
            for color in ['W', 'U', 'B', 'R', 'G']:
                # Regular symbols
                devotion[color] += cost.count(f'{{{color}}}') * quantity
                # Hybrid symbols (count each color in hybrid)
                devotion[color] += cost.count(f'{color}/') * quantity
                devotion[color] += cost.count(f'/{color}') * quantity
        
        return devotion
    
    def _update_color_pie_chart(self, distribution):
        """Update the color distribution pie chart."""
        self.pie_figure.clear()
        ax = self.pie_figure.add_subplot(111)
        
        # Filter out zero values
        labels = []
        sizes = []
        colors = []
        
        color_order = ['W', 'U', 'B', 'R', 'G', 'Multicolor', 'Colorless']
        
        for color in color_order:
            count = distribution.get(color, 0)
            if count > 0:
                if color in self.COLOR_NAMES:
                    labels.append(f"{self.COLOR_NAMES[color]}\n({count})")
                    colors.append(self.COLOR_HEX[color])
                elif color == 'Multicolor':
                    labels.append(f"Multicolor\n({count})")
                    colors.append('#FFD700')  # Gold
                else:
                    labels.append(f"{color}\n({count})")
                    colors.append(self.COLOR_HEX.get(color, '#999999'))
                sizes.append(count)
        
        if not sizes:
            ax.text(0.5, 0.5, 'No cards in deck', 
                   ha='center', va='center', transform=ax.transAxes)
        else:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                  startangle=90, textprops={'fontsize': 9})
            ax.axis('equal')
        
        self.pie_canvas.draw()
    
    def _update_mana_breakdown(self, symbols):
        """Update mana symbol breakdown display."""
        # Clear existing
        while self.mana_layout.count():
            item = self.mana_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        total_symbols = sum(symbols.values())
        
        if total_symbols == 0:
            self.mana_layout.addWidget(QLabel("No mana costs in deck"))
            return
        
        # Display each symbol type
        for symbol, count in sorted(symbols.items(), key=lambda x: -x[1]):
            if count > 0:
                percentage = (count / total_symbols) * 100
                if symbol in self.COLOR_NAMES:
                    label = f"{self.COLOR_NAMES[symbol]} ({symbol}): {count} ({percentage:.1f}%)"
                else:
                    label = f"{symbol}: {count} ({percentage:.1f}%)"
                
                widget = QLabel(label)
                self.mana_layout.addWidget(widget)
    
    def _update_devotion_display(self, devotion):
        """Update devotion display."""
        # Clear existing
        while self.devotion_layout.count():
            item = self.devotion_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        total_devotion = sum(devotion.values())
        
        if total_devotion == 0:
            self.devotion_layout.addWidget(QLabel("No colored mana symbols"))
            return
        
        # Sort by devotion count
        for color in ['W', 'U', 'B', 'R', 'G']:
            count = devotion[color]
            if count > 0:
                percentage = (count / total_devotion) * 100
                label = QLabel(f"{self.COLOR_NAMES[color]}: {count} symbols ({percentage:.1f}%)")
                self.devotion_layout.addWidget(label)
    
    def _update_pip_chart(self, symbols):
        """Update the colored pip distribution bar chart."""
        self.pip_figure.clear()
        ax = self.pip_figure.add_subplot(111)
        
        # Get colored symbols only
        colors_to_plot = ['W', 'U', 'B', 'R', 'G']
        counts = [symbols.get(c, 0) for c in colors_to_plot]
        color_hex = [self.COLOR_HEX[c] for c in colors_to_plot]
        labels = [self.COLOR_NAMES[c] for c in colors_to_plot]
        
        if sum(counts) == 0:
            ax.text(0.5, 0.5, 'No colored mana symbols', 
                   ha='center', va='center', transform=ax.transAxes)
        else:
            bars = ax.bar(labels, counts, color=color_hex, edgecolor='black', linewidth=1)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom', fontsize=9)
            
            ax.set_ylabel('Symbol Count')
            ax.set_title('Colored Mana Symbols')
            
            # Add border to white bar for visibility
            if counts[0] > 0:  # White
                bars[0].set_edgecolor('black')
                bars[0].set_linewidth(2)
        
        self.pip_figure.tight_layout()
        self.pip_canvas.draw()