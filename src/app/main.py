import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

UI_DIR = os.path.join(BASE_DIR, "ui")
APP_DIR = os.path.join(BASE_DIR, "app")
COMMON_DIR = os.path.join(BASE_DIR, "common")
EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")

for path in [UI_DIR, APP_DIR, COMMON_DIR, EXTRACTION_DIR, LINGUISTICS_DIR, LLM_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from PySide6.QtWidgets import QApplication
from main_window import PDFReader


def main():
    app = QApplication(sys.argv)

    window = PDFReader()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()