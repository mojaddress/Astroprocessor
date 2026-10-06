"""
Application Entry Point - PyQt6 Desktop Interface

This module serves as the main entry point for the PyQt6 desktop application,
creating and displaying the main application window.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
from ui_qt.main_window import MainWindow


def register_fonts():
    """Register fonts for proper SVG rendering in frozen executable."""
    # Register system fonts that contain astrological symbols
    # On Windows, Segoe UI Symbol should be available, but register explicitly
    try:
        # Try to register Segoe UI Symbol if available
        if sys.platform == "win32":
            # The font is typically in C:\Windows\Fonts\seguiemj.ttf or similar
            # QFontDatabase will find system fonts automatically on Windows
            pass
    except Exception:
        pass


def main():
    """Initialize and run the PyQt6 application."""
    app = QApplication(sys.argv)
    
    # Register fonts for SVG rendering
    register_fonts()
    
    # Set application properties
    app.setApplicationName("Astro Processor")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Execute the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()