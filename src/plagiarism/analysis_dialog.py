from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
import styles

class AnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przeanalizuj dokument")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(styles.DIALOG_STYLE)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 30)

        header = QHBoxLayout()
        title = QLabel("Przeanalizuj dokument")
        title.setStyleSheet("font-size: 20px; font-weight: bold; border: none;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("border: none; font-size: 18px; color: #666;")
        close_btn.clicked.connect(self.reject)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        layout.addLayout(header)

        layout.addSpacing(20)

        #ramka json
        json_frame = QFrame()
        json_frame.setStyleSheet(styles.JSON_FRAME_STYLE)
        json_layout = QVBoxLayout(json_frame)
        
        json_icon = QLabel("{JSON}")
        json_icon.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 18px; border: none;")
        json_layout.addWidget(json_icon, alignment=Qt.AlignCenter)
        
        txt = QLabel("Przeciągnij tu plik konfiguracyjny")
        txt.setStyleSheet("font-weight: bold; border: none;")
        json_layout.addWidget(txt, alignment=Qt.AlignCenter)
        
        json_layout.addWidget(QLabel("albo", styleSheet="border:none;"), alignment=Qt.AlignCenter)
        
        add_json_btn = QPushButton("+ Dodaj plik konfiguracyjny")
        add_json_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        json_layout.addWidget(add_json_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(json_frame)
        layout.addSpacing(20)

        # Przyciski trybów
        modes_layout = QHBoxLayout()
        self.btn_szybki = QPushButton("Tryb szybki")
        self.btn_szybki.setCheckable(True)
        self.btn_szybki.setStyleSheet(styles.MODE_BTN_STYLE)
        
        self.btn_dokladny = QPushButton("Tryb dokładny")
        self.btn_dokladny.setCheckable(True)
        self.btn_dokladny.setStyleSheet(styles.MODE_BTN_STYLE)
        
        #aktywny tylko jeden
        self.btn_szybki.clicked.connect(lambda: self.btn_dokladny.setChecked(False))
        self.btn_dokladny.clicked.connect(lambda: self.btn_szybki.setChecked(False))

        modes_layout.addWidget(self.btn_szybki)
        modes_layout.addWidget(self.btn_dokladny)
        layout.addLayout(modes_layout)

        layout.addSpacing(20)

        #przycisk do analizuj
        self.analyze_btn = QPushButton("Analizuj")
        self.analyze_btn.setStyleSheet(styles.ANALIZA_BTN_STYLE)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(self.accept)
        layout.addWidget(self.analyze_btn)