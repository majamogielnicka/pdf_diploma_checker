import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
import styles
from pipeline import AnalysisPipeline

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

class PipelineWorker(QThread):
    progress_update = Signal(int, str) 
    finished_success = Signal(object)
    finished_error = Signal(str) 

    def __init__(self, pdf_path, config_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.config_path = config_path

    def run(self):
        try:
            class InputDocument:
                pass
            
            doc = InputDocument()
            doc.pdf_path = self.pdf_path
            pipeline = AnalysisPipeline()
            raport = pipeline.run(doc, progress_callback=self.progress_update.emit)
            
            self.finished_success.emit(raport)
        except Exception as e:
            self.finished_error.emit(str(e))

class AnalysisDialog(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("Przeanalizuj dokument")
        self.setFixedSize(600, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(styles.DIALOG_STYLE)
        
        #zmienna przechowująca wybraną ścieżkę do pliku config
        self.config_file_path = None 
        
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

        #używamy własnej ramki do Drag & Drop
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

        #postęp
        self.progress_widget = QWidget()
        self.progress_widget.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_label = QLabel("Przygotowywanie do analizy...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.pbar.setRange(0, 100)
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

        #przycisk startu
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
        self.drop_label.setStyleSheet("font-weight: bold; border: none; color: #4CAF50;") 
        self.or_label.setVisible(False)
        self.add_json_btn.setText("Zmień plik")

    def _start_analysis(self):
        self.config_widget.setVisible(False)
        self.analyze_btn.setVisible(False)
        self.close_btn.setEnabled(False)
        self.progress_widget.setVisible(True)
        self.title_label.setText("Analizowanie...")
        self.pbar.setValue(0)
        
        #uruchamiamy prawdziwą analizę w tle
        self.worker = PipelineWorker(self.pdf_path, self.config_file_path)
        self.worker.progress_update.connect(self._update_progress)
        self.worker.finished_success.connect(self._on_analysis_success)
        self.worker.finished_error.connect(self._on_analysis_error)
        self.worker.start()

    def _update_progress(self, value, text):
        self.pbar.setValue(value)
        self.progress_label.setText(text)

    def _on_analysis_success(self, final_report):
        self.final_report = final_report
        self.accept()

    def _on_analysis_error(self, error_message):
        self._reset_ui_state()

    def _cancel_analysis(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self._reset_ui_state()

    def _reset_ui_state(self):
        self.pbar.setValue(0)
        self.progress_label.setText("Przygotowywanie do analizy...")
        self.progress_widget.setVisible(False)
        self.config_widget.setVisible(True)
        self.analyze_btn.setVisible(True)
        self.close_btn.setEnabled(True)
        self.title_label.setText("Przeanalizuj dokument")