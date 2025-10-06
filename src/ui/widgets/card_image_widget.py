"""
Widget for displaying card images from Scryfall.
"""
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage
import requests
from io import BytesIO
from pathlib import Path
from src.models.card import Card
from src.api.image_cache import ImageCache  # Import the cache manager

class ImageLoader(QThread):
    """Background thread for loading images with cache support."""
    image_loaded = pyqtSignal(QPixmap)
    error_occurred = pyqtSignal(str)

    def __init__(self, card: Card, cache_dir: Path):
        super().__init__()
        self.card = card
        self.cache_dir = cache_dir
        self.cache = ImageCache(cache_dir)

    def run(self):
        """Load image from cache or download if not cached."""
        try:
            # Build cache filename from set code and collector number
            cache_filename = f"{self.card.set_code.lower()}_{self.card.collector_number}.jpg"
            cache_path = self.cache_dir / cache_filename

            # Check if image exists in cache
            if cache_path.exists() and cache_path.is_file():
                # Load from cache
                pixmap = QPixmap(str(cache_path))
                if not pixmap.isNull():
                    self.image_loaded.emit(pixmap)
                    return
                # If pixmap is null, cache file might be corrupted, fall through to download

            # Cache miss or corrupted - download from Scryfall
            image_url = self.get_card_image_url()
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Save to cache first
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'wb') as f:
                f.write(response.content)

            # Then load into QPixmap
            image_data = BytesIO(response.content)
            image = QImage()
            image.loadFromData(image_data.getvalue())
            pixmap = QPixmap.fromImage(image)
            
            if pixmap.isNull():
                raise Exception("Failed to create pixmap from image data")
                
            self.image_loaded.emit(pixmap)

        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")

    def get_card_image_url(self) -> str:
        """Get Scryfall image URL for card."""
        if hasattr(self.card, 'scryfall_id') and self.card.scryfall_id:
            return f"https://api.scryfall.com/cards/{self.card.scryfall_id}?format=image&version=normal"
        else:
            set_code = self.card.set_code.lower()
            collector_number = self.card.collector_number
            return f"https://api.scryfall.com/cards/{set_code}/{collector_number}?format=image&version=normal"


class CardImageWidget(QWidget):
    """Widget to display card images with local cache support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_card = None
        self.loader = None
        
        # Set up cache directory
        self.cache_dir = Path(__file__).parent.parent.parent.parent / "data" / "card_images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setMinimumSize(200, 280)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.image_label)

        # Card name label
        self.name_label = QLabel("No card selected")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.name_label)

        self.show_placeholder()

    def show_placeholder(self):
        """Show placeholder when no card is selected."""
        self.image_label.setText("🃏\n\nHover over a card\nto see its image")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 5px;
                color: #888;
                font-size: 14px;
            }
        """)
        self.name_label.setText("No card selected")

    def set_card(self, card: Card):
        """Load and display card image from cache or download."""
        if card == self.current_card:
            return

        self.current_card = card
        self.name_label.setText(card.name)

        # Cancel previous loader if running
        if self.loader and self.loader.isRunning():
            self.loader.terminate()
            self.loader.wait()

        # Show loading message
        self.image_label.setText("Loading...")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 5px;
                color: #888;
            }
        """)

        # Load image in background (cache-aware)
        self.loader = ImageLoader(card, self.cache_dir)
        self.loader.image_loaded.connect(self.display_image)
        self.loader.error_occurred.connect(self.show_error)
        self.loader.start()

    def display_image(self, pixmap: QPixmap):
        """Display the loaded image."""
        # Scale image to fit widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 5px;
            }
        """)

    def show_error(self, error_msg: str):
        """Show error message."""
        self.image_label.setText(f"❌\n\nFailed to load image\n\n{error_msg}")
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 5px;
                color: #ff6666;
                font-size: 12px;
            }
        """)

    def clear(self):
        """Clear the current image."""
        self.current_card = None
        if self.loader and self.loader.isRunning():
            self.loader.terminate()
            self.loader.wait()
        self.show_placeholder()