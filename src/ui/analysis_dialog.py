import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
import styles

class ConfigDropFrame(QFrame):
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        #sprawdzamy czy przeciągany jest plik z rozszerzeniem .json
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.json'):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.fileDropped.emit(file_path)


class AnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przeanalizuj dokument")
        self.setFixedSize(600, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(styles.DIALOG_STYLE)
        
        #zmienna przechowująca wybraną ścieżkę do pliku config
        self.config_file_path = None 
        
        #logika paska postępu
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.current_step = 0
        self.total_steps = 70
        
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 30)

        #nagłówek
        header = QHBoxLayout()
        self.title_label = QLabel("Przeanalizuj dokument")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; border: none;")
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("border: none; font-size: 18px; color: #666; background: transparent;")
        self.close_btn.clicked.connect(self.reject)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.close_btn)
        self.main_layout.addLayout(header)

        #opcje konfiguracji
        self.config_widget = QWidget()
        config_layout = QVBoxLayout(self.config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)

        self.json_frame = ConfigDropFrame()
        self.json_frame.setStyleSheet(styles.JSON_FRAME_STYLE)
        json_layout = QVBoxLayout(self.json_frame)
        
        self.json_icon = QLabel("{JSON}")
        self.json_icon.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 18px; border: none;")
        json_layout.addWidget(self.json_icon, alignment=Qt.AlignCenter)
        
        self.drop_label = QLabel("Przeciągnij tu plik konfiguracyjny", styleSheet="font-weight: bold; border: none;")
        json_layout.addWidget(self.drop_label, alignment=Qt.AlignCenter)
        
        self.or_label = QLabel("albo", styleSheet="border:none;")
        json_layout.addWidget(self.or_label, alignment=Qt.AlignCenter)
        
        self.add_json_btn = QPushButton("+ Dodaj plik konfiguracyjny")
        self.add_json_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_json_btn.setCursor(Qt.PointingHandCursor)
        json_layout.addWidget(self.add_json_btn, alignment=Qt.AlignCenter)
        config_layout.addWidget(self.json_frame)

        self.add_json_btn.clicked.connect(self._open_file_dialog)
        self.json_frame.fileDropped.connect(self._set_config_file)

        #wybór trybów
        modes_layout = QHBoxLayout()
        self.btn_szybki = QPushButton("Tryb szybki")
        self.btn_szybki.setCheckable(True)
        self.btn_szybki.setChecked(True)
        self.btn_szybki.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_dokladny = QPushButton("Tryb dokładny")
        self.btn_dokladny.setCheckable(True)
        self.btn_dokladny.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_szybki.clicked.connect(lambda: self.btn_dokladny.setChecked(False))
        self.btn_dokladny.clicked.connect(lambda: self.btn_szybki.setChecked(False))
        modes_layout.addWidget(self.btn_szybki)
        modes_layout.addWidget(self.btn_dokladny)
        config_layout.addLayout(modes_layout)

        self.main_layout.addWidget(self.config_widget)

        #postep
        self.progress_widget = QWidget()
        self.progress_widget.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_label = QLabel("Trwa analiza dokumentu...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.pbar.setRange(0, self.total_steps)
        self.pbar.setValue(0)
        
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setStyleSheet(styles.DELETE_BTN_STYLE)
        self.cancel_btn.clicked.connect(self._cancel_analysis)
        
        progress_layout.addStretch()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.pbar)
        progress_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        progress_layout.addStretch()
        
        self.main_layout.addWidget(self.progress_widget)

        #Przycisk startu
        self.analyze_btn = QPushButton("Analizuj")
        self.analyze_btn.setStyleSheet(styles.ANALIZA_BTN_STYLE)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.main_layout.addWidget(self.analyze_btn)

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik konfiguracyjny", "", "JSON Files (*.json)")
        if path:
            self._set_config_file(path)

    def _set_config_file(self, path):
        self.config_file_path = path
        nazwa = os.path.basename(path)
        
        self.drop_label.setText(f"Załadowano: {nazwa}")
        self.drop_label.setStyleSheet("font-weight: bold; border: none; color: #4CAF50;") # Zmienia kolor na zielony
        self.or_label.setVisible(False)
        self.add_json_btn.setText("Zmień plik")

    def _start_analysis(self):
        self.config_widget.setVisible(False)
        self.analyze_btn.setVisible(False)
        self.close_btn.setEnabled(False)
        self.progress_widget.setVisible(True)
        self.title_label.setText("Analizowanie...")
        self.progress_timer.start(100)

    def _update_progress(self):
        self.current_step += 1
        self.pbar.setValue(self.current_step)
        
        if self.current_step >= self.total_steps:
            self.progress_timer.stop()
            self.accept()

    def _cancel_analysis(self):
        self.progress_timer.stop()
        self.current_step = 0
        self.pbar.setValue(0)
        self.progress_widget.setVisible(False)
        self.config_widget.setVisible(True)
        self.analyze_btn.setVisible(True)
        self.close_btn.setEnabled(True)
        self.title_label.setText("Przeanalizuj dokument")