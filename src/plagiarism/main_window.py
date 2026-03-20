import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QLabel, QPushButton, QSplitter, 
    QLineEdit, QStackedWidget, QFileDialog
)
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

from select_text import SelectablePdfView
from start_page import StartPage
from saving_files import saving_files
import styles

class PDFReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analizator PDF")
        self.resize(1300, 900)
        self.manager = saving_files()
        self.document = QPdfDocument(self)
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.start_page = StartPage()
        self.start_page.add_btn.clicked.connect(self.open_file_dialog)
        self.start_page.fileDropped.connect(self.load_and_switch)
        self.start_page.openRequested.connect(self.load_and_switch)
        self.stack.addWidget(self.start_page)

        self.reader_container = QWidget()
        self.setup_reader_ui()
        self.stack.addWidget(self.reader_container)

        self.refresh_file_list()

    def setup_reader_ui(self):
        layout = QVBoxLayout(self.reader_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        
        self.thumb_area = QScrollArea()
        self.thumb_area.setFixedWidth(160)
        self.thumb_area.setWidgetResizable(True)
        self.thumb_widget = QWidget()
        self.thumb_layout = QVBoxLayout(self.thumb_widget)
        self.thumb_layout.setAlignment(Qt.AlignTop)
        self.thumb_area.setWidget(self.thumb_widget)

        self.pdf_view = SelectablePdfView()
        self.pdf_view.setDocument(self.document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setStyleSheet(styles.PDF_VIEW_STYLE)
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.update_page_input)

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

    def _create_toolbar(self):
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(styles.TOOLBAR_STYLE)
        l = QHBoxLayout(toolbar)
        
        self.back_btn = QPushButton("<")
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setStyleSheet("font-size: 20px; border: none; background: transparent;")
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
        l.addWidget(QLabel("PL | EN", styleSheet=styles.LANG_BTN_STYLE))
        
        return toolbar

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wybierz PDF", "", "PDF Files (*.pdf)")
        if path: self.load_and_switch(path)

    def load_and_switch(self, path):
        nazwa = os.path.basename(path)
        self.manager.dodaj_prace(nazwa, path, "inzynierska")
        
        self.load_pdf(path)
        self.stack.setCurrentIndex(1)
        
        self.refresh_file_list()

    def refresh_file_list(self):
        #Pobiera dane z managera i odświeża widok StartPage.
        pliki = self.manager.data.get("prace", [])
        self.start_page.render_doc_list(pliki)

    def load_pdf(self, path):
        self.document.load(path)
        if self.document.pageCount() > 0:
            self.title_label.setText(os.path.basename(path))
            self.total_pages_label.setText(f" / {self.document.pageCount()} ")
            self.generate_thumbnails()
            self.pdf_view.setZoomFactor(1.0)
            self.zoom_label.setText("100%")

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

    def zoom_in(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() * 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def zoom_out(self):
        self.pdf_view.setZoomFactor(self.pdf_view.zoomFactor() / 1.1)
        self.zoom_label.setText(f"{int(self.pdf_view.zoomFactor()*100)}%")

    def update_page_input(self, idx):
        self.page_input.setText(str(idx + 1))
