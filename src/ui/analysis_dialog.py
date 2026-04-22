import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
import styles

current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))
redaction_path = os.path.join(project_root, "analysis", "modules", "redaction")

if 'runall_configuration_check' in sys.modules:
    del sys.modules['runall_configuration_check']

sys.path.insert(0, redaction_path)

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
    finished_success = Signal(dict) 
    finished_error = Signal(str) 

    def __init__(self, pdf_path, config_path, use_llm):
        super().__init__()
        self.pdf_path = pdf_path
        self.config_path = config_path
        self.use_llm = use_llm

    def run(self):
        try:
            from app.entry import run_analysis_for_pdf
            
            raport_koncowy = run_analysis_for_pdf(
                pdf_path=self.pdf_path, 
                config_path=self.config_path,
                progress_callback=self.progress_update.emit,
                use_llm=self.use_llm
            )
            
            raport_z_obiektami = getattr(raport_koncowy, "linguistics_errors", [])
            
            ui_report = []
            for blad in raport_z_obiektami:
                
                if isinstance(blad, dict):
                    numer_strony = blad.get('page', blad.get('page_number', blad.get('page_start', 1)))
                    bbox = blad.get('bbox', blad.get('bounding_box', None))
                    pojedyncze_x = blad.get('x', None)
                    pojedyncze_y = blad.get('y', None)
                    err_coord = blad.get('error_coordinate', None) 
                    
                    kategoria = blad.get('category', blad.get('ruleId', 'Błąd językowy'))
                    tekst = blad.get('content', blad.get('text', blad.get('matched_text', '[Brak tekstu]')))
                    komentarz = blad.get('message', blad.get('msg', blad.get('comments', 'Znaleziono błąd.')))
                else:
                    numer_strony = getattr(blad, 'page', getattr(blad, 'page_number', getattr(blad, 'page_start', 1)))
                    bbox = getattr(blad, 'bbox', getattr(blad, 'bounding_box', None))
                    pojedyncze_x = getattr(blad, 'x', None)
                    pojedyncze_y = getattr(blad, 'y', None)
                    err_coord = getattr(blad, 'error_coordinate', None)
                    
                    kategoria = getattr(blad, 'category', getattr(blad, 'ruleId', 'Błąd językowy'))
                    tekst = getattr(blad, 'content', getattr(blad, 'text', getattr(blad, 'matched_text', '[Brak tekstu]')))
                    komentarz = getattr(blad, 'message', getattr(blad, 'msg', getattr(blad, 'comments', 'Znaleziono błąd.')))

                if not isinstance(numer_strony, int) or numer_strony <= 0:
                    numer_strony = 1
                
                x, y, w, h = 50.0, 50.0, 20.0, 20.0 
                
                if err_coord and isinstance(err_coord, (list, tuple)) and len(err_coord) >= 2:
                    x, y = float(err_coord[0]), float(err_coord[1])
                    w, h = 20.0, 20.0
                elif pojedyncze_x is not None and pojedyncze_y is not None:
                    x, y = float(pojedyncze_x), float(pojedyncze_y)
                    w, h = 20.0, 20.0
                elif isinstance(bbox, (list, tuple)):
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        x, y = float(x1), float(y1)
                        w, h = float(x2 - x1), float(y2 - y1)
                    elif len(bbox) == 2:
                        x, y = float(bbox[0]), float(bbox[1])
                        w, h = 20.0, 20.0
                
                if w <= 0: w = 20.0
                if h <= 0: h = 20.0

                ui_report.append({
                    "strona": numer_strony,
                    "kategoria": str(kategoria),
                    "znaleziony_tekst": str(tekst),
                    "komentarz": str(komentarz),
                    "wspolrzedne": {
                        "x": x, "y": y, "w": w, "h": h
                    }
                })
            
            sota_data = getattr(raport_koncowy, "llm_result", None)

            dane_dla_ui = {
                "bledy": ui_report,
                "sota": sota_data if isinstance(sota_data, dict) else None
            }
            
            self.finished_success.emit(dane_dla_ui)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_error.emit(str(e))

class AnalysisDialog(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("Przeanalizuj dokument")
        self.setFixedSize(600, 520)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(styles.DIALOG_STYLE)
        
        self.config_file_path = None 
        
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 30)

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
        
        czy_dokladny = self.btn_dokladny.isChecked()
        
        self.worker = PipelineWorker(self.pdf_path, self.config_file_path, use_llm=czy_dokladny)
        
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