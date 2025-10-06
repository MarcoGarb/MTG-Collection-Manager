""" MTG Collection Manager - Main Entry Point """
import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """Launch the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("MTG Collection Manager")

    window = MainWindow()
    window.show()

    # PyQt5 uses exec_()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()