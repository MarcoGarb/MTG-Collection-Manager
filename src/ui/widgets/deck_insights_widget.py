"""
Widget displaying deck insights using unified analyzer.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QScrollArea, QProgressBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.models.deck import Deck
from src.ai.deck_analyzer import DeckAnalyzer


class DeckInsightsWidget(QWidget):
    """Widget showing deck strategic insights."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = None
        self.analyzer = DeckAnalyzer()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        
        # Header
        header = QLabel("🔍 Deck Insights")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Card Draw
        draw_group = QGroupBox("Card Advantage")
        draw_layout = QVBoxLayout()
        self.draw_count_label = QLabel("Card Draw Spells: 0")
        self.draw_count_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        draw_layout.addWidget(self.draw_count_label)
        self.draw_list_label = QLabel("")
        self.draw_list_label.setWordWrap(True)
        draw_layout.addWidget(self.draw_list_label)
        draw_group.setLayout(draw_layout)
        layout.addWidget(draw_group)
        
        # Removal
        removal_group = QGroupBox("Removal & Interaction")
        removal_layout = QVBoxLayout()
        self.removal_count_label = QLabel("Removal Spells: 0")
        self.removal_count_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        removal_layout.addWidget(self.removal_count_label)
        self.removal_types_layout = QVBoxLayout()
        removal_layout.addLayout(self.removal_types_layout)
        removal_group.setLayout(removal_layout)
        layout.addWidget(removal_group)
        
        # Threats vs Answers
        balance_group = QGroupBox("Threats vs Answers Balance")
        balance_layout = QVBoxLayout()
        self.threats_label = QLabel("Threats: 0")
        balance_layout.addWidget(self.threats_label)
        self.threats_bar = QProgressBar()
        self.threats_bar.setMaximum(100)
        self.threats_bar.setTextVisible(True)
        self.threats_bar.setFormat("Threats: %p%")
        balance_layout.addWidget(self.threats_bar)
        self.answers_label = QLabel("Answers: 0")
        balance_layout.addWidget(self.answers_label)
        self.answers_bar = QProgressBar()
        self.answers_bar.setMaximum(100)
        self.answers_bar.setTextVisible(True)
        self.answers_bar.setFormat("Answers: %p%")
        balance_layout.addWidget(self.answers_bar)
        self.balance_analysis_label = QLabel("")
        self.balance_analysis_label.setWordWrap(True)
        balance_layout.addWidget(self.balance_analysis_label)
        balance_group.setLayout(balance_layout)
        layout.addWidget(balance_group)
        
        # Ramp
        ramp_group = QGroupBox("Mana Acceleration")
        ramp_layout = QVBoxLayout()
        self.ramp_count_label = QLabel("Ramp Spells: 0")
        self.ramp_count_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        ramp_layout.addWidget(self.ramp_count_label)
        self.ramp_list_label = QLabel("")
        self.ramp_list_label.setWordWrap(True)
        ramp_layout.addWidget(self.ramp_list_label)
        ramp_group.setLayout(ramp_layout)
        layout.addWidget(ramp_group)
        
        # Win Conditions
        wincon_group = QGroupBox("Win Conditions")
        wincon_layout = QVBoxLayout()
        self.wincon_label = QLabel("")
        self.wincon_label.setWordWrap(True)
        wincon_layout.addWidget(self.wincon_label)
        wincon_group.setLayout(wincon_layout)
        layout.addWidget(wincon_group)
        
        # Format Analysis
        format_group = QGroupBox("Format Analysis")
        format_layout = QVBoxLayout()
        self.format_analysis_label = QLabel("")
        self.format_analysis_label.setWordWrap(True)
        format_layout.addWidget(self.format_analysis_label)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
    
    def set_deck(self, deck: Deck):
        """Update widget with deck data."""
        self.deck = deck
        self.update_display()
    
    def update_display(self):
        """Update all insight displays using unified analyzer."""
        if not self.deck:
            return
        
        # Use unified analyzer
        self.analyzer = DeckAnalyzer(self.deck)
        analysis = self.analyzer.analyze_deck()
        
        # Update displays with analysis results
        self._update_card_draw_display(analysis['card_draw'])
        self._update_removal_display(analysis['removal'], analysis['removal_count'])
        self._update_threats_answers_display(
            analysis['threats'], 
            analysis['threats_count'],
            analysis['answers'],
            analysis['answers_count']
        )
        self._update_ramp_display(analysis['ramp'])
        self._update_wincon_display(analysis['threats'], analysis['card_types'])
        self._update_format_analysis()
    
    def _update_card_draw_display(self, draw_cards):
        """Update card draw display."""
        total_draw = sum(dc.quantity for dc in draw_cards)
        self.draw_count_label.setText(f"Card Draw Spells: {total_draw}")
        
        if draw_cards:
            card_names = [f"{dc.quantity}x {dc.card.name}" for dc in sorted(draw_cards, key=lambda x: -x.quantity)[:10]]
            self.draw_list_label.setText(", ".join(card_names))
        else:
            self.draw_list_label.setText("⚠ No card draw detected - consider adding some!")
    
    def _update_removal_display(self, removal_types, total_removal):
        """Update removal display."""
        # Clear existing
        while self.removal_types_layout.count():
            item = self.removal_types_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.removal_count_label.setText(f"Removal Spells: {total_removal}")
        
        type_labels = {
            'creature_removal': 'Creature Removal',
            'board_wipes': 'Board Wipes',
            'counterspells': 'Counterspells',
            'discard': 'Discard',
            'other': 'Other Removal'
        }
        
        for removal_type, cards in removal_types.items():
            if cards:
                count = sum(dc.quantity for dc in cards)
                label = QLabel(f"  • {type_labels[removal_type]}: {count}")
                self.removal_types_layout.addWidget(label)
        
        if total_removal == 0:
            warning = QLabel("⚠ No removal detected - deck may struggle with threats!")
            warning.setStyleSheet("color: orange;")
            self.removal_types_layout.addWidget(warning)
    
    def _update_threats_answers_display(self, threats, threat_count, answers, answer_count):
        """Update threats vs answers display."""
        total = threat_count + answer_count
        
        if total > 0:
            threat_percent = int((threat_count / total) * 100)
            answer_percent = int((answer_count / total) * 100)
        else:
            threat_percent = 0
            answer_percent = 0
        
        self.threats_label.setText(f"Threats: {threat_count} cards")
        self.threats_bar.setValue(threat_percent)
        
        self.answers_label.setText(f"Answers: {answer_count} cards")
        self.answers_bar.setValue(answer_percent)
        
        # Analysis
        if threat_count == 0 and answer_count == 0:
            analysis = "⚠ Unable to determine threat/answer balance"
        elif threat_count > answer_count * 2:
            analysis = "⚡ Aggressive deck - lots of threats, few answers"
            self.threats_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff4444; }")
        elif answer_count > threat_count * 2:
            analysis = "🛡️ Controlling deck - lots of answers, few threats"
            self.answers_bar.setStyleSheet("QProgressBar::chunk { background-color: #4444ff; }")
        else:
            analysis = "⚖️ Balanced deck - good mix of threats and answers"
            self.threats_bar.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
            self.answers_bar.setStyleSheet("QProgressBar::chunk { background-color: #44ff44; }")
        
        self.balance_analysis_label.setText(analysis)
    
    def _update_ramp_display(self, ramp_cards):
        """Update ramp display."""
        total_ramp = sum(dc.quantity for dc in ramp_cards)
        self.ramp_count_label.setText(f"Ramp Spells: {total_ramp}")
        
        if ramp_cards:
            card_names = [f"{dc.quantity}x {dc.card.name}" for dc in sorted(ramp_cards, key=lambda x: -x.quantity)[:8]]
            self.ramp_list_label.setText(", ".join(card_names))
        else:
            self.ramp_list_label.setText("No ramp detected")
    
    def _update_wincon_display(self, threats, card_types):
        """Analyze win conditions."""
        creature_count = sum(dc.quantity for dc in threats if dc.card.is_creature())
        pw_count = card_types.get('planeswalker', 0)
        
        # Find combo pieces
        mainboard = self.deck.get_mainboard_cards()
        combo_cards = []
        for dc in mainboard:
            text = (dc.card.oracle_text or '').lower()
            if 'win the game' in text or 'lose the game' in text:
                combo_cards.append(dc)
        
        wincon_text = []
        if creature_count > 0:
            wincon_text.append(f"• Combat damage ({creature_count} creatures)")
        if pw_count > 0:
            wincon_text.append(f"• Planeswalker ultimates ({pw_count} planeswalkers)")
        if combo_cards:
            combo_names = ", ".join([dc.card.name for dc in combo_cards])
            wincon_text.append(f"• Combo: {combo_names}")
        
        if not wincon_text:
            wincon_text.append("⚠ No clear win condition detected")
        
        self.wincon_label.setText("\n".join(wincon_text))
    
    def _update_format_analysis(self):
        """Provide format-specific analysis."""
        mainboard = self.deck.get_mainboard_cards()
        deck_format = self.deck.format
        mainboard_count = sum(dc.quantity for dc in mainboard)
        
        analysis = []
        
        if deck_format == 'standard':
            analysis.append("Standard Format:")
            if mainboard_count < 60:
                analysis.append("⚠ Deck below 60 cards - add more cards")
            elif mainboard_count > 60:
                analysis.append("⚠ Deck over 60 cards - consider trimming to 60")
            else:
                analysis.append("✓ Correct deck size (60 cards)")
        
        elif deck_format == 'commander':
            analysis.append("Commander Format:")
            commander = self.deck.get_commander()
            if not commander:
                analysis.append("⚠ No commander assigned")
            else:
                analysis.append(f"✓ Commander: {commander.card.name}")
            
            if mainboard_count < 100:
                analysis.append(f"⚠ Deck has {mainboard_count} cards - need {100 - mainboard_count} more")
            elif mainboard_count > 100:
                analysis.append(f"⚠ Deck has {mainboard_count} cards - remove {mainboard_count - 100}")
            else:
                analysis.append("✓ Correct deck size (100 cards)")
        
        elif deck_format == 'modern':
            analysis.append("Modern Format:")
            if mainboard_count < 60:
                analysis.append("⚠ Deck below 60 cards")
            else:
                analysis.append("✓ Deck size OK")
        
        # Land count analysis
        lands = [dc for dc in mainboard if dc.card.is_land()]
        land_count = sum(dc.quantity for dc in lands)
        
        expected_lands = {
            'standard': (24, 26),
            'modern': (22, 24),
            'commander': (35, 40),
            'pauper': (18, 22),
            'legacy': (18, 22),
            'vintage': (16, 20),
            'brawl': (24, 28)
        }
        
        if deck_format in expected_lands:
            min_lands, max_lands = expected_lands[deck_format]
            if land_count < min_lands:
                analysis.append(f"⚠ Low land count ({land_count}) - consider {min_lands}-{max_lands}")
            elif land_count > max_lands:
                analysis.append(f"⚠ High land count ({land_count}) - typical is {min_lands}-{max_lands}")
            else:
                analysis.append(f"✓ Good land count ({land_count})")
        
        self.format_analysis_label.setText("\n".join(analysis))