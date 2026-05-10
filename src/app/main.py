import sys
import os

from common.path import resource_path
BASE_DIR = resource_path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

UI_DIR = os.path.join(BASE_DIR, "ui")
APP_DIR = os.path.join(BASE_DIR, "app")
COMMON_DIR = os.path.join(BASE_DIR, "common")

for path in [BASE_DIR, UI_DIR, APP_DIR, COMMON_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtWidgets import QApplication
from main_window import PDFReader

def main():
    app = QApplication(sys.argv)
    window = PDFReader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()