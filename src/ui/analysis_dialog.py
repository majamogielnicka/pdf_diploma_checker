import sys
import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QWidget, QFileDialog, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QPixmap, QIcon
import styles

from common.path import resource_path


class FileBadge(QFrame):
    """ Widget displaying info about JSON config file with a delete button"""
    removed = Signal()

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setStyleSheet(styles.FILE_BADGE_FRAME)
        self.setFixedHeight(90)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        self.icon_label = QLabel()
        icon_path = resource_path(os.path.join("ui", "assets", "file_json.svg"))
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("📄")
            self.icon_label.setStyleSheet("font-size: 24px; border: none;")
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setScaledContents(False)
        self.icon_label.setStyleSheet(styles.FILE_BADGE_INNER_LABELS)

        text_container = QWidget()
        text_container.setStyleSheet(styles.FILE_BADGE_INNER_LABELS)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.name_label = QLabel(filename)
        self.name_label.setStyleSheet(styles.FILE_BADGE_NAME_LABEL)

        self.info_label = QLabel("Plik konfiguracyjny JSON")
        self.info_label.setStyleSheet(styles.FILE_BADGE_INFO_LABEL)
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.info_label)

        self.del_btn = QPushButton()
        self.del_btn.setFixedSize(30, 30)
        
        trash_path = resource_path(os.path.join("ui", "assets", "trash.svg"))
        if os.path.exists(trash_path):
            self.del_btn.setIcon(QIcon(trash_path))
            self.del_btn.setIconSize(QSize(20, 20))
        else:
            self.del_btn.setText("usuń")
        
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet(styles.ICON_BUTTON_STYLE)
        self.del_btn.clicked.connect(self.removed.emit)

        layout.addWidget(self.icon_label)
        layout.addWidget(text_container)
        layout.addStretch()
        layout.addWidget(self.del_btn)


class ConfigDropFrame(QFrame):
    """drag-and-drop for JSON files"""
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        """accepts only .json"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.json'):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event):
        """Handles the drop event and gets the file path of the dropped JSON"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.fileDropped.emit(file_path)

class PipelineWorker(QThread):
    """thread that handles the background processing of the PDF analysis"""
    progress_update = Signal(int, str) 
    finished_success = Signal(dict) 
    finished_error = Signal(str) 

    def __init__(self, pdf_path, config_path, use_llm, language):
        super().__init__()
        self.pdf_path = pdf_path
        self.config_path = config_path
        self.use_llm = use_llm
        self.language = language

    def run(self):
        """Runs the analysis, downloads language files, parses coordinates/bounding boxes and gives results"""
        try:
            self.progress_update.emit(5, "Sprawdzanie i pobieranie wymagań językowych...")
            from setup import download_specific_language
            download_specific_language(self.language)

            self.progress_update.emit(10, "Uruchamianie silnika analizy...")
            from app.entry import run_analysis_for_pdf
            
            final_report = run_analysis_for_pdf(
                pdf_path=self.pdf_path, 
                config_path=self.config_path,
                progress_callback=self.progress_update.emit,
                use_llm=self.use_llm,
                language=self.language
            )
            
            report_objects = getattr(final_report, "linguistics_errors", [])
            ui_report = []
            for error in report_objects:
                
                if isinstance(error, dict):
                    page_nr = error.get('page', error.get('page_number', error.get('page_start', 1)))
                    bbox = error.get('bbox', error.get('bounding_box', None))
                    single_x = error.get('x', None)
                    single_y = error.get('y', None)
                    err_coord = error.get('error_coordinate', None) 
                    
                    category = error.get('category', error.get('ruleId', 'Błąd językowy'))
                    text = error.get('content', error.get('text', error.get('matched_text', '[Brak textu]')))
                    comment = error.get('message', error.get('msg', error.get('comments', 'Znaleziono błąd.')))
                else:
                    page_nr = getattr(error, 'page', getattr(error, 'page_number', getattr(error, 'page_start', 1)))
                    bbox = getattr(error, 'bbox', getattr(error, 'bounding_box', None))
                    single_x = getattr(error, 'x', None)
                    single_y = getattr(error, 'y', None)
                    err_coord = getattr(error, 'error_coordinate', None)
                    
                    category = getattr(error, 'category', getattr(error, 'ruleId', 'Błąd językowy'))
                    text = getattr(error, 'content', getattr(error, 'text', getattr(error, 'matched_text', '[Brak textu]')))
                    comment = getattr(error, 'message', getattr(error, 'msg', getattr(error, 'comments', 'Znaleziono błąd.')))

                if not isinstance(page_nr, int) or page_nr <= 0:
                    page_nr = 1
                
                x, y, w, h = 50.0, 50.0, 20.0, 20.0 
                
                if err_coord and isinstance(err_coord, list) and len(err_coord) > 0:
                    first_coord = err_coord[0]
                    if isinstance(first_coord, dict) and "coordinates" in first_coord:
                        bbox_list = first_coord["coordinates"]
                        if len(bbox_list) >= 4:
                            x1, y1, x2, y2 = bbox_list[:4]
                            x, y = float(x1), float(y1)
                            w, h = float(x2 - x1), float(y2 - y1)
                        
                        if first_coord.get("page", -1) != -1:
                            page_nr = first_coord["page"]
                            
                elif isinstance(bbox, (list, tuple)):
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = bbox
                        x, y = float(x1), float(y1)
                        w, h = float(x2 - x1), float(y2 - y1)
                    elif len(bbox) == 2:
                        x, y = float(bbox[0]), float(bbox[1])
                        
                elif single_x is not None and single_y is not None:
                    x, y = float(single_x), float(single_y)
                
                if w <= 0: w = 20.0
                if h <= 0: h = 20.0

                ui_report.append({
                    "page": page_nr,
                    "category": str(category),
                    "found_text": str(text),
                    "comment": str(comment),
                    "coords": {
                        "x": x, "y": y, "w": w, "h": h
                    }
                })
            
            sota_data = getattr(final_report, "llm_result", None)

            ui_data = {
                "errors": ui_report,
                "sota": sota_data if isinstance(sota_data, dict) else None,
                "language": self.language 
            }
            
            self.finished_success.emit(ui_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_error.emit(str(e))

class AnalysisDialog(QDialog):
    """dialog window allowing configuration and running the document analysis. Allows JSON file upload, language selection, and analysis mode switching"""
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("Przeanalizuj dokument")
        self.setFixedSize(800, 700)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(styles.DIALOG_STYLE)
        
        self.config_file_path = None 
        self.setup_ui()

    def _check_gpu_vram(self):
        """Sprawdza dostępność i pamięć VRAM karty graficznej. Zwraca: (Nazwa_GPU, VRAM_w_GB)"""
        try:
            import torch
            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                name = torch.cuda.get_device_name(device)
                vram_gb = torch.cuda.get_device_properties(device).total_memory / (1024**3)
                return name, vram_gb
        except Exception:
            pass
        
        try:
            import subprocess
            creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creation_flags
            )
            if result.returncode == 0:
                output = result.stdout.strip().split('\n')[0]
                name, vram_mb = output.split(',')
                vram_gb = float(vram_mb.strip()) / 1024.0
                return name.strip(), vram_gb
        except Exception:
            pass

        return None, 0.0

    def setup_ui(self):
        """Sets up the layout"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 30)
        self.main_layout.setSpacing(12)

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
        config_layout.setSpacing(12)

        self.json_frame = ConfigDropFrame()
        self.json_frame.setStyleSheet(styles.JSON_FRAME_STYLE)
        self.json_frame.setFixedHeight(240)
        json_inner_layout = QVBoxLayout(self.json_frame)
        json_inner_layout.setSpacing(6)

        self.json_icon = QLabel("{JSON}")
        self.json_icon.setFixedSize(60, 60)
        self.json_icon.setAlignment(Qt.AlignCenter)
        self.json_icon.setStyleSheet(styles.JSON_ICON_CIRCLE)
        self.drop_label = QLabel("Przeciągnij tu plik konfiguracyjny", styleSheet="font-weight: bold; border: none;")
        self.add_json_btn = QPushButton("+ Dodaj plik konfiguracyjny")
        self.add_json_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.add_json_btn.setCursor(Qt.PointingHandCursor)

        json_inner_layout.addStretch()
        json_inner_layout.addWidget(self.json_icon, alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(self.drop_label, alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(QLabel("albo", styleSheet="border:none;"), alignment=Qt.AlignCenter)
        json_inner_layout.addWidget(self.add_json_btn, alignment=Qt.AlignCenter)
        json_inner_layout.addStretch()
        config_layout.addWidget(self.json_frame)

        self.badge_container = QWidget()
        self.badge_container.setStyleSheet("border: none;")
        self.badge_layout = QVBoxLayout(self.badge_container)
        self.badge_layout.setContentsMargins(0, 0, 0, 0)
        self.badge_container.setVisible(False)
        config_layout.addWidget(self.badge_container)

        lang_section = QVBoxLayout()
        lang_section.setSpacing(4)
        lang_title = QLabel("Język pisania pracy:")
        lang_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        
        lang_buttons_layout = QHBoxLayout()
        self.btn_lang_pl = QPushButton("Polski (PL)")
        self.btn_lang_pl.setCheckable(True)
        self.btn_lang_pl.setChecked(True)
        self.btn_lang_pl.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_lang_pl.setFixedHeight(45)
        
        self.btn_lang_en = QPushButton("Angielski (EN)")
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_en.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_lang_en.setFixedHeight(45)
        
        self.btn_lang_pl.clicked.connect(lambda: self.btn_lang_en.setChecked(False))
        self.btn_lang_en.clicked.connect(lambda: self.btn_lang_pl.setChecked(False))
        
        lang_buttons_layout.addWidget(self.btn_lang_pl)
        lang_buttons_layout.addWidget(self.btn_lang_en)
        lang_section.addWidget(lang_title)
        lang_section.addLayout(lang_buttons_layout)
        config_layout.addLayout(lang_section)

        mode_section = QVBoxLayout()
        mode_section.setSpacing(4)
        mode_title = QLabel("Tryb analizy:")
        mode_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")

        modes_layout = QHBoxLayout()
        self.btn_szybki = QPushButton("Tryb szybki")
        self.btn_szybki.setCheckable(True)
        self.btn_szybki.setChecked(True)
        self.btn_szybki.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_szybki.setFixedHeight(45)

        self.btn_dokladny = QPushButton("Tryb dokładny")
        self.btn_dokladny.setCheckable(True)
        self.btn_dokladny.setStyleSheet(styles.MODE_BTN_STYLE)
        self.btn_dokladny.setFixedHeight(45)

        self.cb_images = QCheckBox("Analiza obrazów i grafik (wymaga dużo VRAM)")
        self.cb_images.setStyleSheet(styles.CHECKBOX_STYLE)
        self.cb_images.setChecked(True)
        self.cb_images.setVisible(False)

        gpu_name, vram_gb = self._check_gpu_vram()
        self.gpu_info_label = QLabel()
        self.gpu_info_label.setWordWrap(True)
        
        if gpu_name:
            if vram_gb >= 8.0:
                color = "#2CA05A" 
                rec_text = f"Wykryto GPU: <b>{gpu_name}</b> ({vram_gb:.1f} GB VRAM).<br>Tryb dokładny (AI) powinien działać płynnie."
            else:
                color = "#D32F2F" 
                rec_text = f"Wykryto GPU: <b>{gpu_name}</b> ({vram_gb:.1f} GB VRAM).<br><b>Uwaga:</b> Zalecane minimum to 8 GB VRAM. Tryb dokładny może działać powoli lub nie zadziałać."
        else:
             color = "#D32F2F"
             rec_text = "<b>Brak wspieranego GPU (NVIDIA).</b><br>Tryb dokładny użyje procesora (CPU) i analiza będzie trwała bardzo długo."
             
        self.gpu_info_label.setText(rec_text)
        self.gpu_info_label.setStyleSheet(f"font-size: 11px; color: {color}; margin-top: 4px; background: transparent; border: none;")
        self.gpu_info_label.setVisible(False) 

        modes_layout.addWidget(self.btn_szybki)
        modes_layout.addWidget(self.btn_dokladny)

        mode_section.addWidget(mode_title)     
        mode_section.addLayout(modes_layout)  
        mode_section.addWidget(self.cb_images)
        mode_section.addWidget(self.gpu_info_label)

        def _on_szybki_clicked():
            self.btn_dokladny.setChecked(False)
            self.cb_images.setVisible(False)
            self.gpu_info_label.setVisible(False)
            
        def _on_dokladny_clicked():
            self.btn_szybki.setChecked(False)
            self.cb_images.setVisible(True)
            self.gpu_info_label.setVisible(True)
            
        self.btn_szybki.clicked.connect(_on_szybki_clicked)
        self.btn_dokladny.clicked.connect(_on_dokladny_clicked)

        config_layout.addLayout(mode_section)
        config_layout.addStretch(1)
        self.main_layout.addWidget(self.config_widget)

        self.progress_widget = QWidget()
        self.progress_widget.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setSpacing(25)
        
        self.progress_label = QLabel("Przygotowywanie do analizy...")
        self.progress_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        
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
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.main_layout.addWidget(self.analyze_btn)

        self.add_json_btn.clicked.connect(self._open_file_dialog)
        self.json_frame.fileDropped.connect(self._set_config_file)

    def _open_file_dialog(self):
        """Opens a standard dialog to select a config JSON file manually"""
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik konfiguracyjny", "", "JSON Files (*.json)")
        if path: self._set_config_file(path)

    def _set_config_file(self, path):
        """displays the selected configuration file badge and stores the file path"""
        self.config_file_path = path
        
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.json_frame.setFixedHeight(180)
        badge = FileBadge(os.path.basename(path))
        badge.removed.connect(self._remove_config_file)
        self.badge_layout.addWidget(badge)
        self.badge_container.setVisible(True)

    def _remove_config_file(self):
        """Clears the stored configuration file path and hides the file badge from the UI"""
        self.config_file_path = None
        self.badge_container.setVisible(False)
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.json_frame.setFixedHeight(220)
    def _start_analysis(self):
        """checks if there are models"""
        self.config_widget.setVisible(False)
        self.analyze_btn.setVisible(False)
        self.progress_widget.setVisible(True)
        self.title_label.setText("Analizowanie...")
        
        is_detailed = self.btn_dokladny.isChecked()
        choosen_lg = "pl" if self.btn_lang_pl.isChecked() else "en"
                
        self._run_pipeline_worker(is_detailed, choosen_lg)

    def _run_pipeline_worker(self, is_detailed, choosen_lg):
        """Turns PDF analising thread"""
        self.worker = PipelineWorker(self.pdf_path, self.config_file_path, use_llm=is_detailed, language=choosen_lg)
        self.worker.progress_update.connect(self._update_progress)
        self.worker.finished_success.connect(self._on_analysis_success)
        self.worker.finished_error.connect(lambda msg: self.reject())
        self.worker.start()

    def _on_analysis_success(self, final_report):
        """when the background thread completes successfully closes the dialog"""
        self.final_report = final_report
        self.accept()

    def _cancel_analysis(self):
        """Terminates the running background worker thread"""
        if hasattr(self, 'dl_worker') and self.dl_worker.isRunning():
            self.dl_worker.terminate()
            self.dl_worker.wait()
            
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self._reset_ui_state()

    def _reset_ui_state(self):
        """Resets progress indicators and switches the UI view back"""
        self.pbar.setValue(0)
        self.progress_label.setText("Przygotowywanie do analizy...")
        self.progress_widget.setVisible(False)
        self.config_widget.setVisible(True)
        self.analyze_btn.setVisible(True)
        self.close_btn.setEnabled(True)
        self.title_label.setText("Przeanalizuj dokument")

    def _update_progress(self, value, text):
        """Updates the progress bar value and the description label text"""
        self.pbar.setValue(value)
        self.progress_label.setText(text)
