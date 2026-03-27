# main.py
import sys
from PySide6.QtWidgets import QApplication
from main_window import PDFReader

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = PDFReader()
    window.show()
    
    sys.exit(app.exec())
