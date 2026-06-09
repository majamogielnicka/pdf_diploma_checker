import sys
import os
import datetime

import sys
import os
from common.path import resource_path

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

SRC_DIR = os.path.dirname(CURRENT_DIR)

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = SRC_DIR

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

APP_DIR = os.path.join(BASE_DIR, "app")
COMMON_DIR = os.path.join(BASE_DIR, "common")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

if COMMON_DIR not in sys.path:
    sys.path.insert(0, COMMON_DIR)

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
from saving_files import SavingFiles
import styles
from analysis_dialog import AnalysisDialog
from pipeline import AnalysisPipeline

from PySide6.QtWidgets import QFrame
from entry import run_analysis_for_pdf
from common.path import resource_path

class AnalysisWorker(QObject):
    """A worker class that handles the execution of the document analysis pipeline"""
    progress = Signal(int, str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, pdf_path, config_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.config_path = config_path

    def run(self):
        """Executes the document analysis task, mits signals to communicate progress, completion, or potential errors back to the UI thread."""
        try:
            self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))


class PDFReader(QMainWindow):
    """The main window component of the Diploma Checker application. 
    Manages the user interface flow, PDF rendering, background background workers, and view states."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diploma checker")
        self.resize(1300, 600)
        self.manager = SavingFiles()
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
        self.overlay.setStyleSheet(styles.OVERLAY_STYLE)
        self.overlay.hide()

    def start_background_analysis(self, pdf_path, config_path):
        """Spawns a new QThread worker to perform document processing asynchronously."""
        self.analysis_thread = QThread()
        self.worker = AnalysisWorker(pdf_path, config_path)
        self.worker.moveToThread(self.analysis_thread)

        self.analysis_thread.started.connect(self.analysis_worker.run)       
        self.analysis_thread.start()

    def resizeEvent(self, event):
        """Overrides the standard window resize event listener to correctly re-scale"""
        super().resizeEvent(event)
        if hasattr(self, 'overlay')and self.overlay is not None:
            self.overlay.resize(event.size())

    def open_existing_file(self, path):
        """Loads an already listed file from the disk storage and transitions the interface view 
        into the reading/annotation viewport."""
        self.load_pdf(path)
        if self.document.status() == QPdfDocument.Status.Ready:
            errors = self.manager.get_errors(path)
            if errors:
                self.pdf_view.add_errors(errors)
                if hasattr(self.pdf_view, 'update_markers_pos'):
                    self.pdf_view.update_markers_pos()
                else:
                    self.pdf_view.update()
            self.load_ai_analysis()

            self.stack.setCurrentIndex(1)

    def setup_reader_ui(self):
        """Assembles layout components, content areas, sidebar panels, toolbar items, and internal viewport
        mechanics required to draw the active document review suite workspace."""
        layout = QVBoxLayout(self.reader_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Horizontal)
        
        self.thumb_area = QScrollArea()
        self.thumb_area.setFixedWidth(160)
        self.thumb_area.setWidgetResizable(True)
        self.thumb_area.setStyleSheet(styles.THUMB_AREA_STYLE)
        
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
        """Factory method that builds, styles, and links triggers for the top application toolbar"""
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
        back_icon_path = resource_path(os.path.join("ui", "assets", "back.svg"))
        if os.path.exists(back_icon_path):
            self.back_btn.setIcon(QIcon(back_icon_path))
            self.back_btn.setIconSize(QSize(24, 40))
        else:
            self.back_btn.setText("<") 

        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(styles.BACK_BTN_STYLE)
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
        """Opens a native system file dialog filtered for PDF files, allowing the user 
        to select and import a new document into the application index."""
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz PDF", "", "PDF Files (*.pdf)")
        if path: 
            self.load_and_switch(path)

    def load_and_switch(self, path):
        """Imports a new document into the index manager, loads its content, 
        and switches the active UI view stack to the PDF reader interface."""
        self.overlay.show()
        dialog = AnalysisDialog(path, self)
        result = dialog.exec() 

        self.overlay.hide()

        if result == QDialog.Accepted:
            self.load_pdf(path)
            self.manager.add_document(os.path.basename(path), path, "PDF")
            self.refresh_file_list()
            
            final_rep_obj = getattr(dialog, 'final_report', None)
            errors = []
            report_data = None
            
            if isinstance(final_rep_obj, dict):
                errors = final_rep_obj.get("errors", [])
                report_data = final_rep_obj.get("sota", None)
            elif final_rep_obj is not None:
                errors = getattr(final_rep_obj, "linguistics_errors", [])
                report_data = getattr(final_rep_obj, "llm_result", None)

            self.manager.save_errors(path, errors)
            self.manager.save_ai_result(path, report_data)
            
            self.stack.setCurrentIndex(1)
            
            if errors:
                self.pdf_view.add_errors(errors)
                if hasattr(self.pdf_view, 'update_markers_pos'):
                    self.pdf_view.update_markers_pos()
                else:
                    self.pdf_view.update() 

            if report_data:
                self.update_report_panel(report_data)
            else:
                self.load_ai_analysis()

    def generate_thumbnails(self):
        """Clears out old page cache containers and renders dynamic thumbnail image previews 
        for each separate page of the loaded PDF into the scroll area workspace."""
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
        """Calculates canvas-to-PDF coordinate space transformations based on context menus triggers 
        and appends localized notes into the active viewer tracking system."""
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

    def update_report_panel(self, report_data):
        """Clears the right sidebar verification layout panel and populates it with newly evaluated 
        AI quality metrics, image resolutions, off-topic lists, and lexical sentence stats."""
        import os
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QIcon

        for i in reversed(range(1, self.right_panel.layout().count())): 
            item = self.right_panel.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.right_panel.layout().removeItem(item)

        if not report_data:
            report_data = {}

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(content)
        l.setContentsMargins(0, 10, 0, 0) 
        l.setSpacing(12)                  

        content_grade = report_data.get('content_grade')
        if content_grade is not None:
            if isinstance(content_grade, dict):
                grade = content_grade.get('grade', 0.0)
                max_grade = content_grade.get('max_grade', 100.0)
                p_off = content_grade.get('p_off', 0.0)
                off_topic = content_grade.get('off_topic_sections', 0)
            elif isinstance(content_grade, (float, int)):
                grade = float(content_grade)
                max_grade = 100.0
                p_off = 0.0
                off_topic = 0
            else:
                grade = 0.0
                max_grade = 100.0
                p_off = 0.0
                off_topic = 0

            cg_frame = QFrame()
            cg_frame.setStyleSheet(styles.CONTENT_GRADE_FRAME)
            cg_layout = QVBoxLayout(cg_frame)
            cg_layout.setContentsMargins(15, 12, 15, 12)
            cg_layout.setSpacing(4)

            cg_title = QLabel("Ogólna ocena pracy")
            cg_title.setStyleSheet(styles.CONTENT_GRADE_TITLE)

            cg_val = QLabel(f"{grade} <span style='font-size: 16px; color: #666;'>/ {max_grade} pkt</span>")
            cg_val.setStyleSheet(styles.CONTENT_GRADE_VALUE)

            detale_lbl = QLabel(f"Podrozdziały poza tematem: <b>{off_topic}</b> ({p_off}%)")
            detale_lbl.setStyleSheet(styles.CONTENT_GRADE_DETAILS)

            cg_layout.addWidget(cg_title)
            cg_layout.addWidget(cg_val)
            cg_layout.addWidget(detale_lbl)

            off_topic_headings = content_grade.get('off_topic_headings', [])
            if off_topic_headings:
                headings_title = QLabel("Niezgodne z tematem:")
                headings_title.setStyleSheet(styles.OFF_TOPIC_TITLE_STYLE)
                cg_layout.addWidget(headings_title)
                
                for heading in off_topic_headings:
                    lbl_heading = QLabel(f"• {heading}")
                    lbl_heading.setWordWrap(True)
                    lbl_heading.setStyleSheet(styles.OFF_TOPIC_ITEM_STYLE)
                    cg_layout.addWidget(lbl_heading)

            l.addWidget(cg_frame)
        else:
            none_label = QLabel("Brak danych analizy merytorycznej")
            none_label.setStyleSheet(styles.AI_NONE_LABEL_STYLE)
            l.addWidget(none_label)

        def create_badge_row(label_text, is_met):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)

            lbl = QLabel(label_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(styles.ROW_LABEL_CLEAN)
            

            badge = QFrame()
            badge.setFixedHeight(26)
            badge_layout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(2, 0, 10, 0)

            icon_circle = QLabel()
            icon_circle.setFixedSize(20, 20)
            icon_circle.setAlignment(Qt.AlignCenter)

            if is_met:
                badge.setStyleSheet(styles.BADGE_FRAME_SUCCESS)
                tick_path = resource_path(os.path.join("ui", "assets", "tick.svg"))
                if os.path.exists(tick_path):
                    icon_circle.setPixmap(QIcon(tick_path).pixmap(QSize(12, 12)))
                else:
                    icon_circle.setText("V")
                icon_circle.setStyleSheet(styles.BADGE_ICON_SUCCESS)
                text_lbl = QLabel("Tak")
            else:
                badge.setStyleSheet(styles.BADGE_FRAME_ERROR)
                cross_path = resource_path(os.path.join("ui", "assets", "cross.svg"))
                if os.path.exists(cross_path):
                    icon_circle.setPixmap(QIcon(cross_path).pixmap(QSize(10, 10)))
                else:
                    icon_circle.setText("X")
                icon_circle.setStyleSheet(styles.BADGE_ICON_ERROR)
                text_lbl = QLabel("Nie")

            text_lbl.setStyleSheet(styles.BADGE_TEXT_DEFAULT)
            badge_layout.addWidget(icon_circle)
            badge_layout.addWidget(text_lbl)
            row_layout.addWidget(lbl, stretch=1)
            row_layout.addWidget(badge, alignment=Qt.AlignRight)
            return row_widget

        graphics_container = QWidget()
        graphics_layout = QVBoxLayout(graphics_container)
        graphics_layout.setContentsMargins(0, 4, 0, 0)
        graphics_layout.setSpacing(6)

        graphics_header = QLabel("Weryfikacja rysunków i grafik")
        graphics_header.setStyleSheet(styles.GRAPHICS_HEADER_STYLE)
        graphics_layout.addWidget(graphics_header)

        quality_errors = report_data.get('jakosc_obrazkow', [])
        font_errors = report_data.get('czcionki_obrazkow', [])

        if not quality_errors:
            graphics_layout.addWidget(create_badge_row("Jakość obrazów (rozdzielczość/czytelność)", True))
        else:
            graphics_layout.addWidget(create_badge_row(f"Jakość obrazów (Błędy: {len(quality_errors)})", False))

        if not font_errors:
            graphics_layout.addWidget(create_badge_row("Spójność czcionek na rysunkach", True))
        else:
            graphics_layout.addWidget(create_badge_row(f"Spójność czcionek (Błędy: {len(font_errors)})", False))
        img_data = report_data.get("image_analysis", {})
        raster_nums = img_data.get("raster_numbers", [])
        
        if raster_nums:
            raster_widget = QWidget()
            raster_box_layout = QVBoxLayout(raster_widget)
            raster_box_layout.setContentsMargins(5, 5, 5, 5)
            raster_box_layout.setSpacing(4)
            
            raster_title = QLabel("Wykryte rysunki rastrowe w dokumencie:")
            raster_title.setStyleSheet("color: #555; font-size: 11px; font-weight: bold; background: transparent;")
            raster_box_layout.addWidget(raster_title)
            tags_container = QWidget()
            tags_layout = QHBoxLayout(tags_container)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(6)
            tags_layout.setAlignment(Qt.AlignLeft)
            
            for num in raster_nums:
                num_tag = QLabel(f"Rys. {num}")
                num_tag.setStyleSheet(styles.RASTER_TAG_STYLE)
                tags_layout.addWidget(num_tag)
            
            tags_layout.addStretch()
            raster_box_layout.addWidget(tags_container)
            graphics_layout.addWidget(raster_widget)
        l.addWidget(graphics_container)

        stats_data = report_data.get("statystyki_zdan")
        if stats_data:
            stats_container = QWidget()
            stats_vbox = QVBoxLayout(stats_container)
            stats_vbox.setContentsMargins(0, 4, 0, 0)
            stats_vbox.setSpacing(6)

            stats_header = QLabel("Statystyki składniowe zdań")
            stats_header.setStyleSheet(styles.STATS_HEADER_STYLE)
            stats_vbox.addWidget(stats_header)

            stats_frame = QFrame()
            stats_frame.setStyleSheet(styles.STATS_FRAME_STYLE)
            stats_layout = QVBoxLayout(stats_frame)
            stats_layout.setContentsMargins(12, 10, 12, 10)
            stats_layout.setSpacing(6)

            def create_stat_row(name, val):
                row = QWidget()
                row_l = QHBoxLayout(row)
                row_l.setContentsMargins(0, 0, 0, 0)
                lbl_name = QLabel(name)
                lbl_name.setStyleSheet(styles.STATS_ROW_NAME)
                lbl_val = QLabel(f"<b>{val}</b>")
                lbl_val.setStyleSheet(styles.STATS_ROW_VALUE)
                row_l.addWidget(lbl_name)
                row_l.addWidget(lbl_val)
                return row

            stats_layout.addWidget(create_stat_row("Strona czynna (zalecana):", stats_data.get("active_ratio", "0%")))
            stats_layout.addWidget(create_stat_row("Strona bierna:", stats_data.get("passive_ratio", "0%")))
            stats_layout.addWidget(create_stat_row("Równoważniki zdań:", stats_data.get("verbless_ratio", "0%")))
            
            stats_vbox.addWidget(stats_frame)
            l.addWidget(stats_container)

        l.addStretch()
        
        self.raport_btn = QPushButton("Pobierz dokładny raport")
        self.raport_btn.setCursor(Qt.PointingHandCursor)
        self.raport_btn.setStyleSheet(styles.RAPORT_BTN_STYLE)
        self.raport_btn.clicked.connect(self.generate_detailed_report)
        l.addWidget(self.raport_btn)

        self.right_panel.layout().addWidget(content)   

    def zoom_in(self):
        """Increases the zoom multiplier of the document graphics viewport and updates the status logs."""
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def zoom_out(self):
        """Decreases the zoom multiplier of the document graphics viewport and updates the status logs."""
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def update_page_input(self, idx):
        """Listens to continuous page navigation triggers and syncs current page indexes back to 
        the display box."""
        self.page_input.setText(str(idx + 1))

    def export_pdf_with_annotations(self):
        """Compiles both automated evaluation remarks and user annotation labels together, draws 
        native PyMuPDF shapes or sticky notes, and saves the verified copy as a new PDF file."""
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
            
            errors_do_zapisu = self.manager.get_errors(self.current_pdf_path)

            for err in errors_do_zapisu:
                try:
                    page_num = int(err.get("page", err.get("strona", 1)))
                    if 0 <= page_num < len(doc):
                        page = doc[page_num]
                        coords = err.get("coords", err.get("wspolrzedne", {}))
                        
                        x = float(coords.get("x", 0))
                        y = float(coords.get("y", 0))
                        w = float(coords.get("w", 0))
                        h = float(coords.get("h", 0))
                        
                        kat = str(err.get('category', err.get('kategoria', 'Błąd')))
                        msg = str(err.get('comment', err.get('komentarz', '')))
                        txt = str(err.get('found_text', err.get('znaleziony_tekst', '')))
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
                    print(f"Błąd przy eksporcie błędu automatycznego: {e}")

            saved_comments = self.manager.get_comments(self.current_pdf_path)
            for notatka in saved_comments:
                try:
                    page_idx = int(notatka.get("strona", 1))
                    if 0 <= page_idx < len(doc):
                        page = doc[page_idx]
                        coords = notatka.get("wspolrzedne", {})
                        x = float(coords.get("x", 0))
                        y = float(coords.get("y", 0))
                        w = float(coords.get("w", 0))
                        h = float(coords.get("h", 0))
                        tresc_komentarza = notatka.get('tekst_komentarza', '')

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
                            annot.set_colors(stroke=(0.2, 0.6, 1.0)) 
                            annot.set_info({"title": "Mój komentarz"})
                            annot.update()
                except Exception as e:
                    print(f"Błąd przy eksporcie notatki użytkownika: {e}")

            doc.save(save_path)
            doc.close()
            QMessageBox.information(self, "Sukces", f"PDF z uwagami został zapisany:\n{save_path}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd eksportu:\n{str(e)}")

    def save_custom_comment(self, comment_data):
        """Passes a newly created runtime comment annotation map structure over to the 
        file index data persistence system."""
        if hasattr(self, 'current_pdf_path') and self.current_pdf_path:
            self.manager.save_comment(self.current_pdf_path, comment_data)

    def load_custom_comments(self):
        """Flushes all drawing visual highlights, gathers annotated history registries linked 
        with this file path, and re-paints markers on top of the layout workspace canvas."""
        self.pdf_view.clear_comments()
        if not hasattr(self, 'current_pdf_path') or not self.current_pdf_path:
            return

        saved_comments = self.manager.get_comments(self.current_pdf_path)
        for c_data in saved_comments:
            coords = c_data.get("wspolrzedne", {})
            if coords.get("w", 0) > 0:
                from select_text import HighlightBox
                box = HighlightBox(c_data, self.pdf_view.viewport())
                box.is_error = False
                box.setStyleSheet(styles.HIGHLIGHT_BOX_CUSTOM_COMMENT_STYLE)
                self.pdf_view.highlight_boxes.append(box)

            from select_text import CommentMarker
            marker = CommentMarker(c_data, self.pdf_view.viewport())
            self.pdf_view.comment_markers.append(marker)

        self.pdf_view.update_markers_pos()


    def generate_detailed_report(self):
        """Builds a comprehensive multi-page standalone validation PDF report, inserting customized 
        TrueType text streams, criteria checkpoints, image tracking logs, and syntax metrics."""
        report_data = None
        if hasattr(self, 'current_pdf_path'):
            for p in self.manager.data.get("documents", []):
                if p.get('local_path') == self.current_pdf_path:
                    report_data = p.get("sota_result")
                    break

        if not report_data:
            QMessageBox.warning(self, "Ostrzezenie", "Brak danych szczegolowej analizy merytorycznej dla tego dokumentu.")
            return

        default_name = f"Raport_Merytoryczny_{os.path.basename(self.current_pdf_path)}"
        save_path, _ = QFileDialog.getSaveFileName(self, "Zapisz Raport Szczegolowy", default_name, "Pliki PDF (*.pdf)")
        
        if not save_path:
            return

        try:
            report_pdf = fitz.open()
            page = report_pdf.new_page()
            
            font_path = resource_path(os.path.join("ui", "assets", "Roboto-Regular.ttf"))
            font_bold_path = resource_path(os.path.join("ui", "assets", "Roboto-Bold.ttf"))

            if os.path.exists(font_path) and os.path.exists(font_bold_path):
                page.insert_font(fontname="roboto", fontfile=font_path, encoding=0)
                page.insert_font(fontname="roboto-bold", fontfile=font_bold_path, encoding=0)
                f_main = "roboto"
                f_bold = "roboto-bold"
            else:
                f_main = "helv"
                f_bold = "hebo"

            pos_y = 50
            margin = 50

            def check_new_page(y_coord, pdf_doc, current_page):
                if y_coord > 750:
                    new_p = pdf_doc.new_page()
                    if os.path.exists(font_path) and os.path.exists(font_bold_path):
                        new_p.insert_font(fontname="roboto", fontfile=font_path, encoding=0)
                        new_p.insert_font(fontname="roboto-bold", fontfile=font_bold_path, encoding=0)
                        nonlocal f_main, f_bold
                        f_main = "roboto"
                        f_bold = "roboto-bold"
                    return 50, new_p
                return y_coord, current_page
            
            def wrap_text(text, max_len=90):
                words = text.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= max_len:
                        current_line += (word + " ")
                    else:
                        lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())
                return lines
            
            page.insert_text((margin, pos_y), "Szczegółowy Raport Analizy Merytorycznej", 
                             fontsize=22, fontname=f_bold, color=(0.13, 0.58, 0.95))
            pos_y += 45
            page.insert_text((margin, pos_y), f"Dokument: {os.path.basename(self.current_pdf_path)}", 
                             fontsize=12, fontname=f_main, color=(0.2, 0.2, 0.2))
            pos_y += 40
            
            content_grade = report_data.get('content_grade')
            has_llm_data = content_grade is not None

            if has_llm_data:
                if isinstance(content_grade, dict):
                    grade = content_grade.get('grade', 0)
                    max_g = content_grade.get('max_grade', 100)
                    off_topic = content_grade.get('off_topic_sections', 0)
                    p_off = content_grade.get('p_off', 0)
                    off_topic_headings = content_grade.get('off_topic_headings', [])
                else:
                    grade = content_grade
                    max_g = 100
                    off_topic = 0
                    p_off = 0
                    off_topic_headings = []

                page.insert_text((margin, pos_y), "Ogólna ocena merytoryczna", 
                                 fontsize=14, fontname=f_bold)
                pos_y += 25
                page.insert_text((margin, pos_y), f"Wynik punktowy: {grade} / {max_g} pkt", 
                                 fontsize=12, fontname=f_main)
                pos_y += 20
                page.insert_text((margin, pos_y), 
                                 f"Podrozdziały poza tematem: {off_topic} ({p_off}%)", 
                                 fontsize=11, fontname=f_main)
                pos_y += 25

                if off_topic > 0 and off_topic_headings:
                    page.insert_text((margin, pos_y), "Zidentyfikowane sekcje niezgodne z celem pracy:", 
                                     fontsize=11, fontname=f_bold, color=(0.86, 0.2, 0.27))
                    pos_y += 18
                    for heading in off_topic_headings:
                        pos_y, page = check_new_page(pos_y, report_pdf, page)
                        wrapped_heading = wrap_text(str(heading), 85)
                        for idx, line in enumerate(wrapped_heading):
                            pos_y, page = check_new_page(pos_y, report_pdf, page)
                            prefix = "- " if idx == 0 else "  "
                            page.insert_text((margin + 15, pos_y), f"{prefix}{line}", fontsize=10, fontname=f_main)
                            pos_y += 14
                    pos_y += 15
                else:
                    pos_y += 15

                pos_y, page = check_new_page(pos_y, report_pdf, page)
                page.insert_text((margin, pos_y), "Weryfikacja merytoryczna rozdziału teoretycznego", 
                                 fontsize=14, fontname=f_bold)
                pos_y += 25
                
                chapter_title = report_data.get('tytul', 'Brak tytułu')
                page.insert_text((margin, pos_y), f"Analizowany rozdział: {chapter_title}", 
                                 fontsize=12, fontname=f_main)
                pos_y += 20
                
                score = report_data.get('ocena', 0)
                page.insert_text((margin, pos_y), f"Poziom realizacji wytycznych: {score}%", 
                                 fontsize=12, fontname=f_main)
                pos_y += 30

                criteria = [
                    ("Analiza i ocena istniejących rozwiązań:", report_data.get('r1')),
                    ("Wskazanie luki badawczej lub problemu naukowego:", report_data.get('r2')),
                    ("Synteza i krytyczne porównanie metod:", report_data.get('r3'))
                ]

                for label, met in criteria:
                    pos_y, page = check_new_page(pos_y, report_pdf, page)
                    status = "TAK" if met else "NIE"
                    color = (0.17, 0.62, 0.35) if met else (0.86, 0.2, 0.27)
                    page.insert_text((margin + 20, pos_y), f"{label} {status}", 
                                     fontsize=11, fontname=f_bold if met else f_main, color=color)
                    pos_y += 20

            else:
                page.insert_text((margin, pos_y), "Ogólna ocena merytoryczna (AI)", 
                                 fontsize=14, fontname=f_bold)
                pos_y += 25
                page.insert_text((margin, pos_y), "Analiza została pominięta (wybrano Tryb Szybki).", 
                                 fontsize=11, fontname=f_main, color=(0.5, 0.5, 0.5))
                pos_y += 25

            pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
            img_data = report_data.get("image_analysis", {})
            has_images_checked = img_data.get('total', 0) > 0

            if has_images_checked:
                pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
                page.insert_text((margin, pos_y), "Ocena jakości obrazów (DPI i czytelność)", fontsize=14, fontname=f_bold)
                pos_y += 25

                quality_errors = report_data.get('jakosc_obrazkow', [])
                if not quality_errors:
                    page.insert_text((margin, pos_y), "Wszystkie obrazy mają odpowiednią jakość i czytelność.", 
                                     fontsize=11, fontname=f_main, color=(0.17, 0.62, 0.35))
                    pos_y += 25
                else:
                    page.insert_text((margin, pos_y), f"Wykryto problemy z jakością w {len(quality_errors)} obrazach:", 
                                     fontsize=11, fontname=f_main, color=(0.86, 0.2, 0.27))
                    pos_y += 20
                    for err in quality_errors:
                        pos_y, page = check_new_page(pos_y, report_pdf, page)
                        rys = err.get("rysunek", "Nieznany rysunek")
                        fmt = err.get("format", "Brak formatu")
                        powody = err.get("powody_odrzucenia", [])
                        
                        page.insert_text((margin + 15, pos_y), f"{rys} (Format: {fmt}):", fontsize=11, fontname=f_bold)
                        pos_y += 16
                        for powod in powody:
                            wrapped_powod = wrap_text(powod, 85)
                            for idx, line in enumerate(wrapped_powod):
                                pos_y, page = check_new_page(pos_y, report_pdf, page)
                                prefix = "- " if idx == 0 else "  "
                                page.insert_text((margin + 25, pos_y), f"{prefix}{line}", fontsize=10, fontname=f_main)
                                pos_y += 14
                        pos_y += 5
                
                pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
                page.insert_text((margin, pos_y), "Spójność czcionek na obrazach", fontsize=14, fontname=f_bold)
                pos_y += 25

                font_errors = report_data.get('czcionki_obrazkow', [])
                if not font_errors:
                    page.insert_text((margin, pos_y), "Brak wykrytych problemów ze spójnością czcionek na rysunkach.", 
                                     fontsize=11, fontname=f_main, color=(0.17, 0.62, 0.35))
                    pos_y += 25
                else:
                    page.insert_text((margin, pos_y), f"Wykryto problemy z czcionkami w {len(font_errors)} elementach:", 
                                     fontsize=11, fontname=f_main, color=(0.86, 0.2, 0.27))
                    pos_y += 20
                    for err in font_errors:
                        if isinstance(err, dict):
                            pos_y, page = check_new_page(pos_y, report_pdf, page)
                            rys = err.get("rysunek", "Nieznany rysunek")
                            errors = err.get("errors", err.get("powody_odrzucenia", [str(err)]))
                            
                            page.insert_text((margin + 15, pos_y), f"{rys}:", fontsize=11, fontname=f_bold)
                            pos_y += 16
                            for b in errors:
                                wrapped_blad = wrap_text(str(b), 85)
                                for idx, line in enumerate(wrapped_blad):
                                    pos_y, page = check_new_page(pos_y, report_pdf, page)
                                    prefix = "- " if idx == 0 else "  "
                                    page.insert_text((margin + 25, pos_y), f"{prefix}{line}", fontsize=10, fontname=f_main)
                                    pos_y += 14
                            pos_y += 5
                        else:
                            wrapped_err = wrap_text(str(err), 85)
                            for idx, line in enumerate(wrapped_err):
                                pos_y, page = check_new_page(pos_y, report_pdf, page)
                                prefix = "- " if idx == 0 else "  "
                                page.insert_text((margin + 15, pos_y), f"{prefix}{line}", fontsize=10, fontname=f_main)
                                pos_y += 14
                            pos_y += 5
            
            else:
                pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
                page.insert_text((margin, pos_y), "Ocena jakości obrazów i czcionek", fontsize=14, fontname=f_bold)
                pos_y += 25
                page.insert_text((margin, pos_y), "Analiza została pominięta na życzenie użytkownika lub dokument nie zawiera grafik.", 
                                 fontsize=11, fontname=f_main, color=(0.5, 0.5, 0.5))
                pos_y += 25
            stats_data = report_data.get("statystyki_zdan")
            
            if stats_data:
                pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
                page.insert_text((margin, pos_y), "Analiza statystyczna struktury zdań", fontsize=14, fontname=f_bold)
                pos_y += 22
                page.insert_text((margin + 15, pos_y), "Struktura gramatyczna i stylistyczna badanej pracy dyplomowej:", fontsize=10, fontname=f_main, color=(0.3, 0.3, 0.3))
                pos_y += 18

                struktura_zdan = [
                    (f"Zdania w stronie czynnej: {stats_data.get('active_ratio', '0%')}", "Zalecana forma wypowiedzi w tekstach naukowych podnosząca dynamikę wywodu."),
                    (f"Zdania w stronie biernej: {stats_data.get('passive_ratio', '0%')}", "Stosowana przy opisie procedur badawczych oraz stanu wiedzy."),
                    (f"Równoważniki zdań: {stats_data.get('verbless_ratio', '0%')}", "Konstrukcje bezorzecznikowe, dopuszczalne głównie w nagłówkach i spisach.")
                ]

                for label, opis in struktura_zdan:
                    pos_y, page = check_new_page(pos_y, report_pdf, page)
                    page.insert_text((margin + 15, pos_y), label, fontsize=10, fontname=f_bold)
                    pos_y += 14
                    pos_y, page = check_new_page(pos_y, report_pdf, page)
                    page.insert_text((margin + 25, pos_y), opis, fontsize=9, fontname=f_main, color=(0.4, 0.4, 0.4))
                    pos_y += 16
            else:
                pos_y, page = check_new_page(pos_y + 15, report_pdf, page)
                page.insert_text((margin, pos_y), "Analiza statystyczna struktury zdań", fontsize=14, fontname=f_bold)
                pos_y += 22
                page.insert_text((margin + 15, pos_y), "Brak dostępnych danych statystycznych (uruchom analizę w Trybie Dokładnym).", fontsize=10, fontname=f_main, color=(0.5, 0.5, 0.5))
                pos_y += 20
            pos_y, page = check_new_page(810, report_pdf, page)
            page.insert_text((margin, 820), f"Data: {datetime.date.today()}", 
                             fontsize=9, fontname=f_main, color=(0.5, 0.5, 0.5))

            report_pdf.save(save_path)
            report_pdf.close()
            
            QMessageBox.information(self, "Sukces", f"Raport zostal zapisany pomyslnie:\n{save_path}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Blad Eksportu", f"Blad podczas generowania raportu:\n{str(e)}")