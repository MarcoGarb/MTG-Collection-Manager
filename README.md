# 🃏 MTG Collection Manager

A comprehensive desktop application for managing Magic: The Gathering card collections, building decks, and creating cube drafts with AI-powered assistance.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15.10-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 📚 Collection Management
- **CSV Import/Export**: Import your collection from CSV files or export for backup
- **Card Database**: SQLite database with comprehensive card information
- **Price Tracking**: Real-time price updates via Scryfall API
- **Image Caching**: Automatic card image downloading and caching
- **Advanced Filtering**: Search by name, type, color, rarity, set, and more
- **Gallery View**: Visual card browsing with thumbnails

### ⚔️ Deck Building
- **Manual Deck Construction**: Drag-and-drop interface for building decks
- **AI Deck Generation**: Intelligent deck building with multiple archetypes:
  - Aggro, Midrange, Control, Combo, Tribal
  - Artifact Aggro, Artifact Combo
- **Deck Analysis**: Comprehensive statistics and insights
- **Format Support**: Standard, Commander, Modern, Legacy, Vintage, Pauper, Brawl
- **Validation**: Automatic deck validation and format compliance
- **Import/Export**: Share decks in various formats

### 🎲 Cube Draft System
- **Cube Builder**: Create and manage custom cubes
- **AI Cube Generation**: Generate balanced cubes with multiple archetypes:
  - Power Cube, Vintage Cube, Legacy Cube, Modern Cube, Pauper Cube, Themed Cube
- **Draft Simulation**: Simulate Winston, Grid, and Rotisserie drafts
- **AI Players**: Draft against AI with different strategies
- **Cube Variants**: Support for Singleton and Peasant cubes
- **Validation**: Ensure cube balance and rule compliance

### 🤖 AI Features
- **Smart Recommendations**: AI-powered card suggestions
- **Archetype Analysis**: Identify deck strategies and synergies
- **Artifact Control**: Intelligent artifact selection based on deck archetype
- **Genetic Algorithm**: Optimized deck and cube generation
- **Theme Support**: Generate themed decks and cubes

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (primary support)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MTG-Collection-Manager.git
   cd MTG-Collection-Manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

### Building Executable (Windows)

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**
   ```bash
   .\build_exe.ps1
   ```

3. **Run the executable**
   ```bash
   .\dist\MTG-Collection-Manager.exe
   ```

## 📖 Usage Guide

### Getting Started

1. **Import Your Collection**
   - Click "Import CSV" to load your card collection
   - Supported formats: Name, Set, Quantity, Foil, Condition
   - The app will automatically fetch card data and images

2. **Build a Deck**
   - Click "⚔️ Deck Builder" to open the deck builder
   - Search and add cards from your collection
   - Use "🤖 Generate (AI)" for AI-assisted deck building
   - Validate your deck for format compliance

3. **Create a Cube**
   - Click "🎲 Cube Builder" to open the cube builder
   - Manually add cards or use AI generation
   - Configure singleton/peasant rules
   - Simulate drafts to test your cube

### AI Deck Generation

The AI deck generator supports multiple archetypes:

- **Aggro**: Fast, creature-focused decks with equipment
- **Midrange**: Balanced, value-oriented strategies
- **Control**: Defensive, late-game focused builds
- **Combo**: Synergy-based, combo-focused decks
- **Tribal**: Creature type-focused strategies
- **Artifact Aggro**: Equipment-heavy aggressive decks
- **Artifact Combo**: Artifact-based combo strategies

### Cube Building

Create cubes with different power levels and themes:

- **Power Cube**: High-power, complex interactions
- **Vintage Cube**: Maximum power level with all cards
- **Legacy Cube**: High power but more balanced
- **Modern Cube**: Medium power, accessible
- **Pauper Cube**: Common cards only, budget-friendly
- **Themed Cube**: Custom themes (graveyard, artifacts, tribal, etc.)

### Cube Variants

- **Singleton**: Each card appears only once (except basic lands)
- **Peasant**: Only common and uncommon cards allowed
- **Combined**: Both singleton and peasant rules

## 🏗️ Project Structure

```
MTG-Collection-Manager/
├── src/
│   ├── ai/                    # AI and machine learning modules
│   │   ├── deck_generator.py  # AI deck generation
│   │   ├── cube_generator.py  # AI cube generation
│   │   ├── cube_draft_simulator.py  # Draft simulation
│   │   └── deck_analyzer.py   # Deck analysis and insights
│   ├── api/                   # External API integrations
│   │   ├── scryfall.py        # Scryfall API client
│   │   └── price_updater.py   # Price update system
│   ├── data/                  # Data management
│   │   ├── database.py        # SQLite database operations
│   │   ├── importer.py        # CSV import functionality
│   │   └── inventory.py       # Collection management
│   ├── models/                # Data models
│   │   ├── card.py           # Card data model
│   │   ├── deck.py           # Deck data model
│   │   └── cube.py           # Cube data model
│   └── ui/                    # User interface
│       ├── main_window.py     # Main application window
│       ├── deck_builder_window.py  # Deck building interface
│       ├── cube_builder_window.py  # Cube building interface
│       └── widgets/           # Custom UI widgets
├── data/                      # Application data
│   ├── collection.db         # SQLite database
│   └── card_images/          # Cached card images
├── dist/                      # Built executables
├── tests/                     # Test files
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md                 # This file
```

## 🔧 Configuration

### Database
The application uses SQLite for data storage. The database file is located at `data/collection.db` and is created automatically on first run.

### Card Images
Card images are cached locally in `data/card_images/` to improve performance and reduce API calls.

### API Keys
The application uses the Scryfall API for card data and pricing. No API key is required as Scryfall provides free access.

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python -m pytest tests/
```

Or run individual test files:

```bash
python tests/test_deck_generator.py
python tests/test_deck_generator_full.py
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install development dependencies: `pip install pytest black flake8`
4. Run tests: `python -m pytest`
5. Format code: `black src/`
6. Lint code: `flake8 src/`

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scryfall API** for comprehensive card data and pricing
- **PyQt5** for the user interface framework
- **Magic: The Gathering** is a trademark of Wizards of the Coast LLC
- **Community** for feedback and suggestions

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/MTG-Collection-Manager/issues) page
2. Create a new issue with detailed information
3. Include your operating system and Python version

## 📊 Statistics

- **Lines of Code**: 10,000+
- **Supported Formats**: 7 (Standard, Commander, Modern, Legacy, Vintage, Pauper, Brawl)
- **AI Archetypes**: 7 deck types + 6 cube types
- **Card Database**: 50,000+ cards with full metadata
- **Languages**: Python 3.8+

---

**Made with ❤️ for the Magic: The Gathering community**

*This project is not affiliated with Wizards of the Coast LLC. Magic: The Gathering is a trademark of Wizards of the Coast LLC.*