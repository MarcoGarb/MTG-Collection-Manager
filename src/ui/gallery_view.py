""" Gallery view displaying cards as a grid of images. """
from PyQt5.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QLabel, QVBoxLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QMutex, QMutexLocker
from PyQt5.QtGui import QPixmap, QFont
from typing import List
from pathlib import Path
from src.models.card import Card
from src.api.scryfall import ScryfallAPI
import requests
import time

# Global rate limiter for Scryfall API
class RateLimiter:
    """Thread-safe rate limiter for API requests."""
    def __init__(self, requests_per_second=5):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0.0
        self.mutex = QMutex()

    def wait(self):
        """Wait if necessary to respect rate limit."""
        locker = QMutexLocker(self.mutex)
        now = time.time()
        time_since_last = now - self.last_request
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        self.last_request = time.time()
        del locker

# Shared rate limiter instance
rate_limiter = RateLimiter(requests_per_second=5)

class CardThumbnailLoader(QThread):
    """Thread for loading card thumbnail with cache-first approach and rate limiting."""
    finished = pyqtSignal(int, object)  # card_index, image_path

    def __init__(self, card_index: int, card: Card, cache_dir: Path):
        super().__init__()
        self.card_index = card_index
        self.card = card
        self.cache_dir = cache_dir
        self.api = ScryfallAPI()
        self._should_stop = False

    def run(self):
        """Load image from cache or download if missing."""
        try:
            cache_filename = f"{self.card.set_code.lower()}_{self.card.collector_number}.jpg"
            cache_path = self.cache_dir / cache_filename

            # Cache hit
            if cache_path.exists() and cache_path.is_file() and cache_path.stat().st_size > 0:
                test_pixmap = QPixmap(str(cache_path))
                if not test_pixmap.isNull():
                    self.finished.emit(self.card_index, cache_path)
                    return

            if self._should_stop:
                return

            # Rate-limit API and fetch data
            rate_limiter.wait()
            if self._should_stop:
                return

            card_data = self.api.get_card_by_set_and_number(
                self.card.set_code, self.card.collector_number
            )
            if not card_data:
                self.finished.emit(self.card_index, None)
                return

            image_url = self.api.get_card_image_url(card_data, size='small')
            if not image_url:
                image_url = self.api.get_card_image_url(card_data, size='normal')
            if not image_url:
                self.finished.emit(self.card_index, None)
                return

            if self._should_stop:
                return

            rate_limiter.wait()
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temp_path = cache_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            if temp_path.stat().st_size > 0:
                temp_path.replace(cache_path)
                self.finished.emit(self.card_index, cache_path)
            else:
                temp_path.unlink()
                self.finished.emit(self.card_index, None)

        except requests.exceptions.HTTPError as e:
            if getattr(e, 'response', None) and e.response.status_code == 429:
                time.sleep(2)
            self.finished.emit(self.card_index, None)
        except requests.exceptions.RequestException:
            self.finished.emit(self.card_index, None)
        except Exception:
            self.finished.emit(self.card_index, None)

    def stop(self):
        """Signal thread to stop gracefully."""
        self._should_stop = True


class CardThumbnail(QWidget):
    """Widget displaying a single card thumbnail."""
    clicked = pyqtSignal(object)  # Emits the card when clicked

    def __init__(self, card: Card, parent=None):
        super().__init__(parent)
        self.card = card

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.setLayout(layout)

        # Image label
        self.image_label = QLabel("Loading...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(146, 204)  # Small card image size
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 8px;
                color: #888;
            }
        """)
        layout.addWidget(self.image_label)

        # Card name
        name_label = QLabel(card.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(146)
        font = QFont()
        font.setPointSize(8)
        name_label.setFont(font)
        layout.addWidget(name_label)

        # Quantity badge (if > 1)
        if card.quantity > 1:
            qty_label = QLabel(f"x{card.quantity}")
            qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_label.setStyleSheet("""
                QLabel {
                    background-color: #4a90e2;
                    color: white;
                    border-radius: 10px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
            """)
            layout.addWidget(qty_label)

        # Price (if available)
        if card.current_price:
            price_label = QLabel(f"${card.current_price:.2f}")
            price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_font = QFont()
            price_font.setPointSize(9)
            price_font.setBold(True)
            price_label.setFont(price_font)
            price_label.setStyleSheet("color: #4CAF50;")
            layout.addWidget(price_label)

        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Hover effect
        self.setStyleSheet("""
            CardThumbnail {
                background-color: #1a1a1a;
                border-radius: 10px;
            }
            CardThumbnail:hover {
                background-color: #2a2a2a;
            }
        """)

    def set_image(self, image_path):
        """Set the card image from path."""
        if not image_path or not image_path.exists():
            self.image_label.setText("No image")
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.image_label.setText("Failed to load")
            return

        # Scale to fit
        scaled = pixmap.scaled(
            146, 204,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def mousePressEvent(self, event):
        """Handle click on card."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.card)


class GalleryView(QWidget):
    """Gallery view displaying cards as image grid with rate-limited loading."""
    card_clicked = pyqtSignal(object)  # Emits card when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards = []
        self.thumbnails = []
        
        # Set up cache directory
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "card_images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.loader_threads = []
        self.max_concurrent_downloads = 3  # Limit concurrent downloads
        self.active_downloads = 0
        self.download_queue = []
        
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Container for grid
        self.container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.container.setLayout(self.grid_layout)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

    def set_cards(self, cards: List[Card]):
        """Display cards in gallery view."""
        self.cards = cards
        self.clear_gallery()

        if not cards:
            # Show empty message
            empty_label = QLabel("No cards to display")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(14)
            empty_label.setFont(font)
            empty_label.setStyleSheet("color: #888;")
            self.grid_layout.addWidget(empty_label, 0, 0)
            return

        # Calculate columns based on width
        columns = max(1, self.width() // 170)  # 146px + margins

        # Create thumbnails
        for i, card in enumerate(cards):
            row = i // columns
            col = i % columns

            thumbnail = CardThumbnail(card)
            thumbnail.clicked.connect(self.card_clicked.emit)
            self.thumbnails.append(thumbnail)
            self.grid_layout.addWidget(thumbnail, row, col)

            # Queue image loading
            self.download_queue.append((i, card, thumbnail))

        # Start loading images with limited concurrency
        self.process_download_queue()

    def process_download_queue(self):
        """Process download queue with limited concurrency."""
        while self.active_downloads < self.max_concurrent_downloads and self.download_queue:
            index, card, thumbnail = self.download_queue.pop(0)
            self.load_thumbnail(index, card, thumbnail)

    def load_thumbnail(self, index: int, card: Card, thumbnail: CardThumbnail):
        """Load thumbnail image in background thread."""
        self.active_downloads += 1
        loader = CardThumbnailLoader(index, card, self.cache_dir)
        loader.finished.connect(lambda idx, path: self.on_thumbnail_loaded(idx, path, thumbnail))
        loader.start()
        self.loader_threads.append(loader)

    def on_thumbnail_loaded(self, index: int, image_path, thumbnail: CardThumbnail):
        """Handle thumbnail loaded."""
        thumbnail.set_image(image_path)
        self.active_downloads -= 1
        
        # Process next item in queue
        QTimer.singleShot(100, self.process_download_queue)  # Small delay between downloads

    def clear_gallery(self):
        """Clear all thumbnails from gallery."""
        # Stop any running loaders gracefully
        for thread in self.loader_threads:
            if hasattr(thread, 'stop'):
                thread.stop()
            if thread.isRunning():
                thread.wait(100)  # Wait briefly
                if thread.isRunning():
                    thread.terminate()
        
        self.loader_threads.clear()
        self.download_queue.clear()
        self.active_downloads = 0

        # Remove all widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.thumbnails.clear()

    def resizeEvent(self, event):
        """Handle window resize to adjust columns."""
        super().resizeEvent(event)