"""
Card detail dialog showing full card information and image.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QGridLayout, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from pathlib import Path
from src.models.card import Card
from src.api.scryfall import ScryfallAPI
from src.api.image_cache import ImageCache


class ImageDownloadThread(QThread):
    """Thread for downloading card image without blocking UI."""
    finished = pyqtSignal(object)  # Emits Path or None
    
    def __init__(self, image_url: str, image_cache: ImageCache):
        super().__init__()
        self.image_url = image_url
        self.image_cache = image_cache
        
    def run(self):
        """Download the image."""
        path = self.image_cache.get_image_path(self.image_url, download=True)
        self.finished.emit(path)


class CardDetailDialog(QDialog):
    """Dialog showing detailed card information and image."""
    
    def __init__(self, card: Card, parent=None):
        super().__init__(parent)
        self.card = card
        self.api = ScryfallAPI()
        self.image_cache = ImageCache()
        self.card_data = None
        self.download_thread = None
        
        self.init_ui()
        self.load_card_data()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"{self.card.name} - Card Details")
        self.setMinimumSize(800, 600)
        
        # Main layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Left side: Card image
        image_layout = QVBoxLayout()
        
        self.image_label = QLabel("Loading image...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(350, 488)  # Standard MTG card aspect ratio
        self.image_label.setStyleSheet("QLabel { background-color: #1a1a1a; border: 1px solid #333; }")
        
        image_layout.addWidget(self.image_label)
        image_layout.addStretch()
        
        main_layout.addLayout(image_layout)
        
        # Right side: Card details
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        details_widget.setLayout(details_layout)
        
        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidget(details_widget)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)
        
        # Card name (title)
        self.name_label = QLabel(self.card.name)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.name_label.setFont(title_font)
        self.name_label.setWordWrap(True)
        details_layout.addWidget(self.name_label)
        
        # Basic info group
        basic_group = self.create_basic_info_group()
        details_layout.addWidget(basic_group)
        
        # Collection info group
        collection_group = self.create_collection_info_group()
        details_layout.addWidget(collection_group)
        
        # Card text group
        self.text_group = QGroupBox("Card Text")
        text_layout = QVBoxLayout()
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setMaximumHeight(150)
        text_layout.addWidget(self.text_display)
        self.text_group.setLayout(text_layout)
        details_layout.addWidget(self.text_group)
        
        # Legalities group (will populate after API call)
        self.legalities_group = QGroupBox("Format Legalities")
        self.legalities_layout = QGridLayout()
        self.legalities_group.setLayout(self.legalities_layout)
        details_layout.addWidget(self.legalities_group)
        
        details_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        details_layout.addWidget(close_btn)
        
        main_layout.addWidget(scroll)
        
    def create_basic_info_group(self):
        """Create basic card information group."""
        group = QGroupBox("Card Information")
        layout = QGridLayout()
        
        row = 0
        
        # Mana cost (will update from API)
        layout.addWidget(QLabel("Mana Cost:"), row, 0)
        self.mana_label = QLabel("Loading...")
        layout.addWidget(self.mana_label, row, 1)
        row += 1
        
        # Type line (will update from API)
        layout.addWidget(QLabel("Type:"), row, 0)
        self.type_label = QLabel("Loading...")
        self.type_label.setWordWrap(True)
        layout.addWidget(self.type_label, row, 1)
        row += 1
        
        # Set
        layout.addWidget(QLabel("Set:"), row, 0)
        set_label = QLabel(f"{self.card.set_code.upper()} #{self.card.collector_number}")
        layout.addWidget(set_label, row, 1)
        row += 1
        
        # Rarity
        layout.addWidget(QLabel("Rarity:"), row, 0)
        rarity_label = QLabel(self.card.rarity.capitalize() if self.card.rarity else "Unknown")
        layout.addWidget(rarity_label, row, 1)
        row += 1
        
        group.setLayout(layout)
        return group
        
    def create_collection_info_group(self):
        """Create collection-specific information group."""
        group = QGroupBox("Your Collection")
        layout = QGridLayout()
        
        row = 0
        
        # Quantity
        layout.addWidget(QLabel("Quantity:"), row, 0)
        qty_label = QLabel(str(self.card.quantity))
        layout.addWidget(qty_label, row, 1)
        row += 1
        
        # Foil
        layout.addWidget(QLabel("Foil:"), row, 0)
        foil_label = QLabel("Yes" if self.card.foil else "No")
        layout.addWidget(foil_label, row, 1)
        row += 1
        
        # Condition
        if self.card.condition:
            layout.addWidget(QLabel("Condition:"), row, 0)
            condition_label = QLabel(self.card.condition.replace('_', ' ').title())
            layout.addWidget(condition_label, row, 1)
            row += 1
        
        # Language
        layout.addWidget(QLabel("Language:"), row, 0)
        lang_label = QLabel(self.card.language.upper())
        layout.addWidget(lang_label, row, 1)
        row += 1
        
        # Purchase price
        if self.card.purchase_price:
            layout.addWidget(QLabel("Purchase Price:"), row, 0)
            purchase_label = QLabel(f"${self.card.purchase_price:.2f}")
            layout.addWidget(purchase_label, row, 1)
            row += 1
        
        # Current price
        if self.card.current_price:
            layout.addWidget(QLabel("Current Price:"), row, 0)
            current_label = QLabel(f"${self.card.current_price:.2f}")
            font = QFont()
            font.setBold(True)
            current_label.setFont(font)
            layout.addWidget(current_label, row, 1)
            row += 1
            
            # Total value
            layout.addWidget(QLabel("Total Value:"), row, 0)
            total_value = self.card.current_price * self.card.quantity
            total_label = QLabel(f"${total_value:.2f}")
            font = QFont()
            font.setBold(True)
            total_label.setFont(font)
            layout.addWidget(total_label, row, 1)
            row += 1
        
        group.setLayout(layout)
        return group
        
    def load_card_data(self):
        """Load additional card data from Scryfall."""
        # Fetch card data
        self.card_data = self.api.get_card_by_set_and_number(
            self.card.set_code,
            self.card.collector_number
        )
        
        if not self.card_data:
            self.image_label.setText("Card not found on Scryfall")
            return
            
        # Update UI with card data
        self.update_card_details()
        
        # Load image
        self.load_card_image()
        
    def update_card_details(self):
        """Update UI with data from Scryfall."""
        if not self.card_data:
            return
            
        # Mana cost
        mana_cost = self.card_data.get('mana_cost', '')
        self.mana_label.setText(mana_cost if mana_cost else 'N/A')
        
        # Type line
        type_line = self.card_data.get('type_line', '')
        self.type_label.setText(type_line if type_line else 'Unknown')
        
        # Oracle text
        oracle_text = self.card_data.get('oracle_text', '')
        if oracle_text:
            self.text_display.setPlainText(oracle_text)
        else:
            self.text_display.setPlainText("No text available")
            
        # Legalities
        self.populate_legalities()
        
    def populate_legalities(self):
        """Populate format legalities."""
        if not self.card_data or 'legalities' not in self.card_data:
            return
            
        legalities = self.card_data['legalities']
        
        # Common formats to display
        formats = ['standard', 'pioneer', 'modern', 'legacy', 'vintage', 'commander', 'pauper']
        
        row = 0
        col = 0
        for format_name in formats:
            if format_name in legalities:
                status = legalities[format_name]
                
                # Format label
                format_label = QLabel(f"{format_name.capitalize()}:")
                self.legalities_layout.addWidget(format_label, row, col * 2)
                
                # Status label with color
                status_label = QLabel(status.capitalize())
                if status == 'legal':
                    status_label.setStyleSheet("color: green; font-weight: bold;")
                elif status == 'not_legal':
                    status_label.setStyleSheet("color: red;")
                else:
                    status_label.setStyleSheet("color: orange;")
                    
                self.legalities_layout.addWidget(status_label, row, col * 2 + 1)
                
                col += 1
                if col >= 2:  # 2 columns
                    col = 0
                    row += 1
                    
    def load_card_image(self):
        """Load card image (with caching)."""
        if not self.card_data:
            return
            
        image_url = self.api.get_card_image_url(self.card_data, size='normal')
        
        if not image_url:
            self.image_label.setText("No image available")
            return
            
        # Check if cached
        if self.image_cache.is_cached(image_url):
            image_path = self.image_cache.get_image_path(image_url, download=False)
            self.display_image(image_path)
        else:
            # Download in background thread
            self.image_label.setText("Downloading image...")
            self.download_thread = ImageDownloadThread(image_url, self.image_cache)
            self.download_thread.finished.connect(self.display_image)
            self.download_thread.start()
            
    def display_image(self, image_path: Path):
        """Display the card image."""
        if not image_path or not image_path.exists():
            self.image_label.setText("Failed to load image")
            return
            
        pixmap = QPixmap(str(image_path))
        
        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
            return
            
        # Scale image to fit label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)