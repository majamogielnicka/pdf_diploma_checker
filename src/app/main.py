import sys
import os

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from common.path import resource_path

UI_DIR = os.path.join(BASE_DIR, "ui")
APP_DIR = os.path.join(BASE_DIR, "app")
COMMON_DIR = os.path.join(BASE_DIR, "common")

for path in [UI_DIR, APP_DIR, COMMON_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from PySide6.QtWidgets import QApplication
from ui.main_window import PDFReader
from setup import check_and_download_requirements

def main():
    app = QApplication(sys.argv)
    check=check_and_download_requirements()
    if not check:
        sys.exit()
    window = PDFReader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()