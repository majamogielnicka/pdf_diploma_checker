import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QWidget, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QPixmap, QIcon
import styles

class FileBadge(QFrame):
    removed = Signal()

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #C4C4C4;
                border-radius: 8px;
                background-color: #FFFFFF;
            }
        """)
        self.setFixedHeight(70)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        self.icon_label = QLabel()
        icon_path = os.path.join("src", "assets", "file_json.svg")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("📄")
            self.icon_label.setStyleSheet("font-size: 24px; border: none;")
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setStyleSheet("border: none;")

        text_container = QWidget()
        text_container.setStyleSheet("border: none;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #000; border: none;")
        
        self.info_label = QLabel("Plik konfiguracyjny JSON")
        self.info_label.setStyleSheet("color: #666; font-size: 12px; border: none;")
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.info_label)

        self.del_btn = QPushButton()
        self.del_btn.setFixedSize(30, 30)
        trash_path = os.path.join("src", "assets", "trash.svg")
        if os.path.exists(trash_path):
            self.del_btn.setIcon(QIcon(trash_path))
            self.del_btn.setIconSize(QSize(20, 20))
        else:
            self.del_btn.setText("usun")
        
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; }
            QPushButton:hover { background-color: #f0f0f0; border-radius: 4px; }
        """)
        self.del_btn.clicked.connect(self.removed.emit)

        layout.addWidget(self.icon_label)
        layout.addWidget(text_container)
        layout.addStretch()
        layout.addWidget(self.del_btn)


class ConfigDropFrame(QFrame):
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
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
        self.main_layout.setSpacing(15)

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
        self.config_widget.setStyleSheet("border: none;")
        config_layout = QVBoxLayout(self.config_widget)
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(15)

        self.json_frame = ConfigDropFrame()
        self.json_frame.setStyleSheet(styles.JSON_FRAME_STYLE)
        self.json_frame.setFixedHeight(180)
        json_inner_layout = QVBoxLayout(self.json_frame)
        
        self.json_icon = QLabel("{JSON}")
        self.json_icon.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 18px; border: none;")
        self.drop_label = QLabel("Przeciągnij tu plik konfiguracyjny", styleSheet="font-weight: bold; border: none;")
        self.add_json_btn = QPushButton("+ Dodaj plik konfiguracyjny")
        self.add_json_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_json_btn.setCursor(Qt.PointingHandCursor)

        json_inner_layout.addWidget(self.json_icon, alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(self.drop_label, alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(QLabel("albo", styleSheet="border:none;"), alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(self.add_json_btn, alignment=Qt.AlignCenter)
        config_layout.addWidget(self.json_frame)

        self.badge_container = QWidget()
        self.badge_container.setStyleSheet("border: none;")
        self.badge_layout = QVBoxLayout(self.badge_container)
        self.badge_layout.setContentsMargins(0, 0, 0, 0)
        self.badge_container.setVisible(False)
        config_layout.addWidget(self.badge_container)

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
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        progress_layout.addWidget(QLabel("Analizowanie dokumentu...", alignment=Qt.AlignCenter))
        progress_layout.addWidget(self.pbar)
        self.main_layout.addWidget(self.progress_widget)

        self.analyze_btn = QPushButton("Analizuj")
        self.analyze_btn.setStyleSheet(styles.ANALIZA_BTN_STYLE)
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.main_layout.addWidget(self.analyze_btn)

        self.add_json_btn.clicked.connect(self._open_file_dialog)
        self.json_frame.fileDropped.connect(self._set_config_file)

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik konfiguracyjny", "", "JSON Files (*.json)")
        if path: self._set_config_file(path)

    def _set_config_file(self, path):
        self.config_file_path = path
        
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        badge = FileBadge(os.path.basename(path))
        badge.removed.connect(self._remove_config_file)
        self.badge_layout.addWidget(badge)
        self.badge_container.setVisible(True)

    def _remove_config_file(self):
        self.config_file_path = None
        self.badge_container.setVisible(False)
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _start_analysis(self):
        if not self.config_file_path:
            pass
        self.config_widget.setVisible(False)
        self.analyze_btn.setVisible(False)
        self.progress_widget.setVisible(True)
        self.title_label.setText("Analizowanie...")
        
        czy_dokladny = self.btn_dokladny.isChecked()
        self.worker = PipelineWorker(self.pdf_path, self.config_file_path, use_llm=czy_dokladny)
        self.worker.progress_update.connect(lambda v, t: self.pbar.setValue(v))
        self.worker.finished_success.connect(self._on_analysis_success)
        self.worker.finished_error.connect(lambda msg: self.reject())
        self.worker.start()

    def _on_analysis_success(self, final_report):
        self.final_report = final_report
        self.accept()