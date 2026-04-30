import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(BASE_DIR, "app")
COMMON_DIR = os.path.join(BASE_DIR, "common")

if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QSplitter,
    QLineEdit, QStackedWidget, QFileDialog, QMessageBox
)
import os
import json
import fitz
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QLabel, QPushButton, QSplitter, 
    QLineEdit, QStackedWidget, QFileDialog, QMessageBox,
    QDialog, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QPointF, QObject, Signal, QThread
from PySide6.QtGui import QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from select_text import SelectablePdfView, CommentMarker, HighlightBox
from start_page import StartPage
from saving_files import saving_files
import styles
from analysis_dialog import AnalysisDialog
from pipeline import AnalysisPipeline

from PySide6.QtWidgets import QFrame
from entry import run_analysis_for_pdf

class AnalysisWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, pdf_path, config_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.config_path = config_path

    def run(self):
        try:
            self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))

class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diploma checker")
        self.resize(1300, 600)
        self.manager = saving_files()
        self.own_comments = []
        self.document = QPdfDocument(self)
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_page = StartPage()
        
        self.start_page.add_btn.clicked.connect(self.open_file_dialog)
        self.start_page.fileDropped.connect(self.load_and_switch)
        
        self.start_page.openRequested.connect(self.open_existing_file)
        
        self.start_page.deleteRequested.connect(self.delete_document)
        self.stack.addWidget(self.start_page)
        
        self.reader_container = QWidget()
        self.setup_reader_ui()
        self.stack.addWidget(self.reader_container)

        self.refresh_file_list()
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 160);") 
        self.overlay.hide()

    def start_background_analysis(self, pdf_path, config_path):
        self.analysis_thread = QThread()
        self.worker = AnalysisWorker(pdf_path, config_path)
        self.worker.moveToThread(self.analysis_thread)

        self.analysis_thread.started.connect(self.worker.run)        
        self.analysis_thread.start()
        print("Wątek wystartował!")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay'):
            self.overlay.resize(event.size())

    def open_existing_file(self, path):
        self.load_pdf(path)
        if self.document.status() == QPdfDocument.Status.Ready:
            self.stack.setCurrentIndex(1)

    def setup_reader_ui(self):
        layout = QVBoxLayout(self.reader_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Horizontal)
        
        self.thumb_area = QScrollArea()
        self.thumb_area.setFixedWidth(160)
        self.thumb_area.setWidgetResizable(True)
        self.thumb_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #E0E0E0; }
            QScrollBar:vertical { border: none; background: transparent; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #C4C4C4; min-height: 30px; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #A0A0A0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        
        self.thumb_widget = QWidget()
        self.thumb_layout = QVBoxLayout(self.thumb_widget)
        self.thumb_layout.setAlignment(Qt.AlignTop)
        self.thumb_area.setWidget(self.thumb_widget)

        self.pdf_view = SelectablePdfView()
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setStyleSheet(styles.PDF_VIEW_STYLE)
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.update_page_input)
        self.pdf_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pdf_view.customContextMenuRequested.connect(self.add_comment)
        self.pdf_view.commentAdded.connect(self.save_custom_comment)

        self.right_panel = QWidget()
        self.right_panel.setFixedWidth(300)
        self.right_panel.setStyleSheet(styles.RIGHT_PANEL_STYLE)
        right_layout = QVBoxLayout(self.right_panel)
        v_label = QLabel("Weryfikacja")
        v_label.setStyleSheet(styles.VERIFY_TITLE_STYLE)
        right_layout.addWidget(v_label)
        right_layout.addStretch()

        splitter.addWidget(self.thumb_area)
        splitter.addWidget(self.pdf_view)
        splitter.addWidget(self.right_panel)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.toolbar.raise_()

    def _create_toolbar(self):

        toolbar = QWidget()
        toolbar.setFixedHeight(70)
        toolbar.setStyleSheet(styles.TOOLBAR_STYLE)
        shadow = QGraphicsDropShadowEffect(toolbar)
        shadow.setBlurRadius(15)    
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)               
        toolbar.setGraphicsEffect(shadow)

        l = QHBoxLayout(toolbar)
        
        self.back_btn = QPushButton()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        back_icon_path = os.path.join(current_dir, "assets", "back.svg")
        if os.path.exists(back_icon_path):
            self.back_btn.setIcon(QIcon(back_icon_path))
            self.back_btn.setIconSize(QSize(24, 40))
        else:
            self.back_btn.setText("<") 

        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px; 
                border: none; 
                background: transparent;
            }
        """)
        self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        l.addWidget(self.back_btn)

        self.title_label = QLabel("Brak dokumentu")
        self.title_label.setStyleSheet(styles.NORMAL_LABEL_STYLE)
        l.addWidget(self.title_label)
        l.addStretch(1)

        self.page_input = QLineEdit("1")
        self.page_input.setFixedWidth(40)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.total_pages_label = QLabel(" / 0 ")
        self.zoom_label = QLabel("100%")
        
        btn_in = QPushButton("+")
        btn_in.setFixedSize(30, 30)
        btn_in.clicked.connect(self.zoom_in)
        
        btn_out = QPushButton("-")
        btn_out.setFixedSize(30, 30)
        btn_out.clicked.connect(self.zoom_out)

        l.addWidget(self.page_input)
        l.addWidget(self.total_pages_label)
        l.addWidget(QLabel(" | ", styleSheet=styles.SEPARATOR_STYLE))
        l.addWidget(btn_out)
        l.addWidget(self.zoom_label)
        l.addWidget(btn_in)
        l.addStretch(1)
        l.addWidget(QLabel(" ", styleSheet=styles.LANG_BTN_STYLE))

        self.export_btn = QPushButton("Pobierz PDF z uwagami")
        self.export_btn.setStyleSheet(styles.BLUE_BUTTON_STYLE)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_pdf_with_annotations)
        l.addWidget(self.export_btn)
        
        return toolbar

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz PDF", "", "PDF Files (*.pdf)")
        if path: 
            self.load_and_switch(path)

    def load_and_switch(self, path):
        self.overlay.show()
        dialog = AnalysisDialog(path, self)
        result = dialog.exec() 

        self.overlay.hide()

        if result == QDialog.Accepted:
            self.load_pdf(path)
            self.manager.dodaj_prace(os.path.basename(path), path, "PDF")
            self.refresh_file_list()
            self.last_report = getattr(dialog, 'final_report', None)
            
            if hasattr(dialog, 'final_report') and dialog.final_report:
                bledy = dialog.final_report.get("bledy", [])
                sota_data = dialog.final_report.get("sota", None)
        
                self.pdf_view.add_errors(bledy)
                self.update_sota_panel(sota_data)
                
            self.stack.setCurrentIndex(1)
            print("Analiza zakończona, widok przełączony.")
    
    def refresh_file_list(self):
        pliki = self.manager.data.get("prace", [])
        self.start_page.render_doc_list(pliki)

    def delete_document(self, path):
        reply = QMessageBox.question(
            self, 'Potwierdzenie', 
            "Czy na pewno chcesz usunąć ten dokument z listy?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.manager.usun_prace(path)
            self.refresh_file_list()

    def load_pdf(self, path):
        if not os.path.exists(path):
            QMessageBox.critical(self, "Błąd", f"Nie odnaleziono pliku:\n{path}")
            return
        self.current_pdf_path = path
        self.document.load(path)
        current_error = self.document.error()
        if current_error == QPdfDocument.Error.IncorrectPassword:
            QMessageBox.warning(self, "Plik zabezpieczony", "Ten PDF wymaga hasła.")
            return
        elif self.document.status() == QPdfDocument.Status.Error:
            QMessageBox.critical(self, "Błąd", "Nie udało się załadować pliku PDF.")
            return

        if self.document.pageCount() > 0:
            self.title_label.setText(os.path.basename(path))
            self.total_pages_label.setText(f" / {self.document.pageCount()} ")
            self.generate_thumbnails()
            self.pdf_view.setZoomFactor(1.0)
            self.zoom_label.setText("100%")
        
            self.load_template_errors()
            self.load_custom_comments()

    def load_template_errors(self):
        json_path = "errors_output3.json"
        if not os.path.exists(json_path):
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bledy = data.get("wykryte_bledy", [])
                self.pdf_view.add_errors(bledy) 
        except Exception as e:
            print(f"Błąd podczas wczytywania błędów: {e}")

    def generate_thumbnails(self):
        for i in reversed(range(self.thumb_layout.count())):
            w = self.thumb_layout.itemAt(i).widget()
            if w: w.setParent(None)
        for i in range(self.document.pageCount()):
            btn = QPushButton()
            btn.setIcon(QPixmap.fromImage(self.document.render(i, QSize(100, 140))))
            btn.setIconSize(QSize(100, 140))
            btn.setFixedSize(110, 150)
            btn.clicked.connect(lambda chk, idx=i: self.pdf_view.pageNavigator().jump(idx, QPointF(0,0), self.pdf_view.zoomFactor()))
            self.thumb_layout.addWidget(btn)

    def add_comment(self, pos):
        if not hasattr(self, 'current_pdf_path') or not self.current_pdf_path:
            return

        if self.pdf_view.selection_box.isVisible() and self.pdf_view.selection_box.geometry().contains(pos):
            return

        tekst, ok = QInputDialog.getMultiLineText(self, "Własny komentarz", "Wpisz treść komentarza:")
        
        if ok and tekst.strip():
            aktualna_strona = self.pdf_view.pageNavigator().currentPage()
            zoom = self.pdf_view.zoomFactor()
            
            scroll_x = self.pdf_view.horizontalScrollBar().value()
            scroll_y = self.pdf_view.verticalScrollBar().value()
            dpi_x, dpi_y = self.pdf_view.logicalDpiX(), self.pdf_view.logicalDpiY()
            
            doc = self.document
            size_pt = doc.pagePointSize(aktualna_strona)
            page_w_px = size_pt.width() * zoom * (dpi_x / 72.0)
            viewport_w = self.pdf_view.viewport().width()
            
            x_start_px = self.pdf_view.documentMargins().left() if self.pdf_view.horizontalScrollBar().maximum() > 0 else (viewport_w - page_w_px) / 2
            
            target_page_y_px = self.pdf_view.documentMargins().top()
            for i in range(aktualna_strona):
                page_size = doc.pagePointSize(i)
                page_h_px = int((page_size.height() * zoom * (dpi_y / 72.0)) + 0.5)
                target_page_y_px += page_h_px + self.pdf_view.pageSpacing()

            pdf_x = ((pos.x() + scroll_x - x_start_px) / zoom) * (72.0 / dpi_x)
            pdf_y = ((pos.y() + scroll_y - target_page_y_px) / zoom) * (72.0 / dpi_y)

            comment_data = {
                "strona": aktualna_strona + 1,
                "wspolrzedne": {"x": pdf_x, "y": pdf_y},
                "tekst_komentarza": tekst.strip(),
                "znaleziony_tekst": "(Komentarz dodany w pustym miejscu)"
            }
            marker = CommentMarker(comment_data, self.pdf_view.viewport())
            self.pdf_view.comment_markers.append(marker)
            self.pdf_view.update_markers_pos()
            self.save_custom_comment(comment_data)

    def update_sota_panel(self, sota_data):
        import os
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QIcon

        for i in reversed(range(1, self.right_panel.layout().count())): 
            item = self.right_panel.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.right_panel.layout().removeItem(item)

        if not sota_data:
            brak_label = QLabel("Brak danych SOTA (Tryb szybki)")
            brak_label.setStyleSheet("color: #7f8c8d; font-style: italic; border: none; margin-top: 15px;")
            self.right_panel.layout().addWidget(brak_label)
            self.right_panel.layout().addStretch()
            return

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 15, 0, 0)
        l.setSpacing(15)
        wynik = sota_data.get('ocena', 0)
        is_good = wynik >= 50
        
        score_frame = QFrame()
        bg_color = "#E8F5E9" if is_good else "#FFEBEE"
        border_color = "#C8E6C9" if is_good else "#FFCDD2"
        text_color = "#2E7D32" if is_good else "#C62828"
        
        score_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
        """)
        score_layout = QVBoxLayout(score_frame)
        score_layout.setContentsMargins(15, 12, 15, 12)
        score_layout.setSpacing(2)
        
        score_title = QLabel("Ogólna ocena SOTA")
        score_title.setStyleSheet("color: #555; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        
        score_val = QLabel(f"{wynik}%")
        score_val.setStyleSheet(f"color: {text_color}; font-size: 28px; font-weight: bold; border: none; background: transparent;")
        
        score_layout.addWidget(score_title)
        score_layout.addWidget(score_val)
        l.addWidget(score_frame)
        tytul_lbl = QLabel(f"<b>Analizowany rozdział:</b><br>{sota_data.get('tytul', 'Brak')}")
        tytul_lbl.setWordWrap(True)
        tytul_lbl.setStyleSheet("color: #333; font-size: 13px; border: none; margin-top: 5px;")
        l.addWidget(tytul_lbl)
        def create_badge_row(label_text, is_met):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)

            lbl = QLabel(label_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #444; font-size: 13px; border: none;")

            badge = QFrame()
            badge.setFixedHeight(26)
            badge_layout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(2, 0, 10, 0)
            badge_layout.setSpacing(6)

            icon_circle = QLabel()
            icon_circle.setAlignment(Qt.AlignCenter)
            icon_circle.setFixedSize(20, 20)

            if is_met:
                badge.setStyleSheet("QFrame { background-color: #D1EEDC; border-radius: 13px; border: none; }")
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                tick_path = os.path.join(current_dir, "assets", "tick.svg")
                if os.path.exists(tick_path):
                    icon_circle.setPixmap(QIcon(tick_path).pixmap(QSize(12, 12)))
                else:
                    icon_circle.setText("✓")
                icon_circle.setStyleSheet("QLabel { background-color: #2CA05A; color: white; border-radius: 10px; font-weight: bold; font-size: 12px; }")
                
                text_lbl = QLabel("Tak")
                text_lbl.setStyleSheet("color: #000; font-weight: bold; font-size: 12px; border: none; background: transparent;")
            else:
                badge.setStyleSheet("QFrame { background-color: #F8D7DA; border-radius: 13px; border: none; }")
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                cross_path = os.path.join(current_dir, "assets", "cross.svg")
                if os.path.exists(cross_path):
                    icon_circle.setPixmap(QIcon(cross_path).pixmap(QSize(10, 10)))
                else:
                    icon_circle.setText("✕")
                icon_circle.setStyleSheet("QLabel { background-color: #DC3545; color: white; border-radius: 10px; font-weight: bold; font-size: 12px; }")
                
                text_lbl = QLabel("Nie")
                text_lbl.setStyleSheet("color: #000; font-weight: bold; font-size: 12px; border: none; background: transparent;")

            badge_layout.addWidget(icon_circle)
            badge_layout.addWidget(text_lbl)

            row_layout.addWidget(lbl, stretch=1)
            row_layout.addWidget(badge, alignment=Qt.AlignRight | Qt.AlignVCenter)
            return row_widget

        l.addWidget(create_badge_row("Ocena istniejących rozwiązań", sota_data.get('r1')))
        l.addWidget(create_badge_row("Wskazanie luki / problemu", sota_data.get('r2')))
        l.addWidget(create_badge_row("Synteza / porównanie metod", sota_data.get('r3')))

        self.right_panel.layout().addWidget(content)
        self.right_panel.layout().addStretch()


    def zoom_in(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def zoom_out(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def update_page_input(self, idx):
        self.page_input.setText(str(idx + 1))

    def export_pdf_with_annotations(self):
        if not hasattr(self, 'current_pdf_path') or not self.current_pdf_path:
            QMessageBox.warning(self, "Uwaga", "Brak załadowanego dokumentu do eksportu.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz PDF z uwagami", 
            f"sprawdzony_{os.path.basename(self.current_pdf_path)}", 
            "PDF Files (*.pdf)"
        )
        
        if not save_path: return

        try:
            doc = fitz.open(self.current_pdf_path)
            
            bledy_do_zapisu = []
            if hasattr(self, 'last_report') and self.last_report:
                bledy_do_zapisu = self.last_report.get("bledy", [])

            for err in bledy_do_zapisu:
                try:
                    page_num = int(err.get("strona", 1)) - 1
                    if 0 <= page_num < len(doc):
                        page = doc[page_num]
                        coords = err.get("wspolrzedne", {})
                        
                        x, y = float(coords.get("x", 0)), float(coords.get("y", 0))
                        w, h = float(coords.get("w", 0)), float(coords.get("h", 0))
                        
                        kat = str(err.get('kategoria', 'Błąd'))
                        msg = str(err.get('komentarz', ''))
                        txt = str(err.get('znaleziony_tekst', ''))
                        opis = f"[{kat}]\n{msg}\n\nTekst: {txt}"
                        
                        if w > 0 and h > 0:
                            rect = fitz.Rect(x, y, x + w, y + h)
                            hl = page.add_highlight_annot(rect)
                            hl.set_colors(stroke=(1.0, 0.85, 0.85)) 
                            hl.set_opacity(0.6) 
                            hl.set_info({"title": "Weryfikacja", "content": opis})
                            hl.update()
                        else:
                            point = fitz.Point(x, y - 15) 
                            annot = page.add_text_annot(point, opis, icon="Comment")
                            annot.set_colors(stroke=(1.0, 0.7, 0.7)) 
                            annot.set_info({"title": "Weryfikacja"})
                            annot.update()
                except Exception as e:
                    print(f"Błąd przy eksporcie błędu: {e}")

            if hasattr(self.pdf_view, 'comment_markers'):
                for marker in self.pdf_view.comment_markers:
                    try:
                        notatka = marker.data
                        page_idx = notatka["strona"] - 1
                        if 0 <= page_idx < len(doc):
                            page = doc[page_idx]
                            coords = notatka["wspolrzedne"]
                            x, y = coords["x"], coords["y"]
                            w, h = coords.get("w", 0), coords.get("h", 0)
                            tresc_komentarza = notatka['tekst_komentarza']

                            if w > 0 and h > 0:
                                rect = fitz.Rect(x, y, x + w, y + h)
                                hl = page.add_highlight_annot(rect)
                                hl.set_colors(stroke=(0.85, 0.92, 1.0)) 
                                hl.set_opacity(0.5)
                                hl.set_info({"title": "Mój komentarz", "content": tresc_komentarza})
                                hl.update()
                            else:
                                point = fitz.Point(x, y - 15)
                                annot = page.add_text_annot(point, tresc_komentarza, icon="Note")
                                annot.set_colors(stroke=(1, 1, 1)) 
                                annot.set_info({"title": "Mój komentarz"})
                                annot.update()
                    except Exception as e:
                        print(f"Błąd przy eksporcie notatki: {e}")

            doc.save(save_path)
            doc.close()
            QMessageBox.information(self, "Sukces", "PDF został zapisany")
                        
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd eksportu:\n{str(e)}")

    def save_custom_comment(self, comment_data):
        if hasattr(self, 'current_pdf_path') and self.current_pdf_path:
            self.manager.zapisz_komentarz(self.current_pdf_path, comment_data)

    def load_custom_comments(self):
        self.pdf_view.clear_comments()
        
        if not hasattr(self, 'current_pdf_path') or not self.current_pdf_path:
            return

        saved_comments = self.manager.pobierz_komentarze(self.current_pdf_path)

        for c_data in saved_comments:
            w = c_data.get("wspolrzedne", {}).get("w", 0)
            h = c_data.get("wspolrzedne", {}).get("h", 0)

            if w > 0 and h > 0:
                box = HighlightBox(c_data, self.pdf_view.viewport())
                self.pdf_view.highlight_boxes.append(box)

            marker = CommentMarker(c_data, self.pdf_view.viewport())
            self.pdf_view.comment_markers.append(marker)

        self.pdf_view.update_markers_pos()