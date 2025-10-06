# src/ui/widgets/card_preview_popup.py
"""Floating popup widget for card image preview (PyQt5-compatible)."""
from io import BytesIO
import requests

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QImage

from src.models.card import Card


class CardPreviewPopup(QWidget):
    """Floating popup that shows a card image near the mouse cursor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_card = None

        # Use PyQt5 flag enums
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        # If you want blurred corners later, set True and adjust style
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._init_ui()

        # Small delay before actually showing to avoid flicker
        self.show_timer = QTimer(self)
        self.show_timer.setSingleShot(True)
        self.show_timer.timeout.connect(self._show_popup)

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        self.image_label = QLabel("Hover a card")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 3px solid #555;
                border-radius: 12px;
                padding: 6px;
                color: #aaa;
            }
        """)
        layout.addWidget(self.image_label)

        # Fixed size suitable for a readable preview
        self.setFixedSize(250, 350)
        self.hide()

    def show_card(self, card: Card, global_pos: QPoint):
        """Schedule showing a preview for the given card at a screen position."""
        # If same card and already visible, skip work
        if self.isVisible() and self.current_card is not None and card == self.current_card:
            return

        self.current_card = card

        # Position with a small offset so it doesn't sit under the cursor
        offset = QPoint(20, 20)
        self.move(global_pos + offset)

        # Debounce rapid hover changes
        self.show_timer.stop()
        self.show_timer.start(250)

    def _show_popup(self):
        if not self.current_card:
            return

        self.image_label.setText("Loading")
        self.show()
        self.raise_()

        # Load image now
        self._load_image(self.current_card)

    def _load_image(self, card: Card):
        """Fetch and render the card image from Scryfall."""
        try:
            image_url = self._get_card_image_url(card)
            if not image_url:
                self.image_label.setText("No image")
                return

            resp = requests.get(image_url, timeout=4)
            resp.raise_for_status()

            img = QImage()
            img.loadFromData(BytesIO(resp.content).getvalue())
            pix = QPixmap.fromImage(img)

            if pix.isNull():
                self.image_label.setText("Image error")
                return

            scaled = pix.scaled(
                240, 340,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

        except Exception as e:
            # Keep error short to avoid UI overflow
            self.image_label.setText(f"Error:\n{str(e)[:60]}")

    def _get_card_image_url(self, card: Card) -> str:
        """Return a direct Scryfall image URL (normal size)."""
        if getattr(card, "scryfall_id", None):
            # Direct by Scryfall ID
            return f"https://api.scryfall.com/cards/{card.scryfall_id}?format=image&version=normal"
        # Fallback by set/collector number
        set_code = (card.set_code or "").lower()
        collector_number = card.collector_number or ""
        if not set_code or not collector_number:
            return ""
        return f"https://api.scryfall.com/cards/{set_code}/{collector_number}?format=image&version=normal"

    def hide_popup(self):
        """Hide and reset current state."""
        self.show_timer.stop()
        self.hide()
        self.current_card = None