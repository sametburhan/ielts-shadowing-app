"""
IELTS Speaking Shadowing Assistant (Duy - Durakla - Tekrar Et)
Application Entry Point.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from src.ui.main_window import MainWindow

def main():
    # Set Windows AppUserModelID so Windows taskbar displays the custom app icon
    if sys.platform == "win32":
        try:
            import ctypes
            app_id = "ielts.speaking.shadowing.assistant.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("IELTS Shadowing Assistant")
    app.setOrganizationName("IELTSCoach")

    # Set default modern clean font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    from src.config import LOGO_PATH, LOGO_ICO_PATH
    icon = None
    if LOGO_ICO_PATH.exists():
        icon = QIcon(str(LOGO_ICO_PATH))
    elif LOGO_PATH.exists():
        icon = QIcon(str(LOGO_PATH))

    if icon:
        app.setWindowIcon(icon)

    window = MainWindow()
    if icon:
        window.setWindowIcon(icon)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
