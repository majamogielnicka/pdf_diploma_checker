import webbrowser
from urllib.parse import quote_plus
from PySide6.QtWidgets import QMenu, QApplication, QRubberBand 
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, Signal, QPointF, QSize
from PySide6.QtGui import QAction
from PySide6.QtPdfWidgets import QPdfView
import styles

class SelectablePdfView(QPdfView):
    textCopied = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selection_box = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.selection_pdf_rect = None 
        self.selection_page_idx = -1
        self.selected_text = ""
        #naprawienie pozycji po scrollu
        self.verticalScrollBar().valueChanged.connect(self.update_selection_box_pos)
        self.horizontalScrollBar().valueChanged.connect(self.update_selection_box_pos)

    #naprawa pozycji po resize okienka
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_selection_box_pos()

    def update_selection_box_pos(self):
        #jesli rysujemy badz nie ma prostokata to nie przeliczamy
        if not self.origin.isNull() or self.selection_page_idx == -1 or not self.selection_pdf_rect:
            return
        
        doc = self.document()
        if not doc or doc.pageCount() <= self.selection_page_idx: return

        dpi_x, dpi_y = self.logicalDpiX(), self.logicalDpiY()
        zoom = self.zoomFactor()

        target_page_y_px = self.documentMargins().top()
        for i in range(self.selection_page_idx):
            size_pt = doc.pagePointSize(i)
            target_page_y_px += (size_pt.height() * zoom * (dpi_y / 72.0)) + self.pageSpacing()

        size_pt = doc.pagePointSize(self.selection_page_idx)
        page_w_px = size_pt.width() * zoom * (dpi_x / 72.0)
        viewport_w = self.viewport().width()
        
        if self.horizontalScrollBar().maximum() > 0:
            x_start_px = self.documentMargins().left()
        else:
            x_start_px = (viewport_w - page_w_px) / 2

        rect_pt = self.selection_pdf_rect
        px_x = x_start_px + (rect_pt.x() * zoom * (dpi_x / 72.0)) - self.horizontalScrollBar().value()
        px_y = target_page_y_px + (rect_pt.y() * zoom * (dpi_y / 72.0)) - self.verticalScrollBar().value()
        px_w = rect_pt.width() * zoom * (dpi_x / 72.0)
        px_h = rect_pt.height() * zoom * (dpi_y / 72.0)

        self.selection_box.setGeometry(int(px_x), int(px_y), int(px_w), int(px_h))
        self.selection_box.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.selection_box.isVisible() and self.selection_box.geometry().contains(event.position().toPoint()):
                self.show_context_menu(event.globalPosition().toPoint())
            return

        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
            self.origin = event.position().toPoint()
            self.selection_box.setGeometry(QRect(self.origin, QSize(0,0)))
            self.selection_box.show()
            self.selected_text = ""
            self.selection_pdf_rect = None
            self.selection_page_idx = -1
            event.accept()
            return
            
        if event.button() == Qt.LeftButton:
            self.selection_box.hide()
            self.selected_text = ""
            self.selection_pdf_rect = None
            self.selection_page_idx = -1

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and event.modifiers() == Qt.ShiftModifier:
            self.selection_box.setGeometry(QRect(self.origin, event.position().toPoint()).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.origin.isNull():
            rect = self.selection_box.geometry()
            self.origin = QPoint()
            self.extract_text(rect)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def extract_text(self, rect):
        
        doc = self.document()
        if not doc or doc.pageCount() == 0: return
        #pobranie danych o aktualnym wyswietlaniu
        v_val = self.verticalScrollBar().value()
        h_val = self.horizontalScrollBar().value()
        dpi_x, dpi_y = self.logicalDpiX(), self.logicalDpiY()

        current_y_px = self.documentMargins().top()
        
        for i in range(doc.pageCount()):
            size_pt = doc.pagePointSize(i)
            page_w_px = size_pt.width() * self.zoomFactor() * (dpi_x / 72.0)
            page_h_px = size_pt.height() * self.zoomFactor() * (dpi_y / 72.0)
            
            center_y_px = rect.center().y() + v_val
            
            if current_y_px <= center_y_px <= current_y_px + page_h_px:
                viewport_w = self.viewport().width()
                x_start_px = self.documentMargins().left() if self.horizontalScrollBar().maximum() > 0 else (viewport_w - page_w_px) / 2
                
                px1 = rect.left() + h_val - x_start_px
                py1 = rect.top() + v_val - current_y_px
                px2 = rect.right() + h_val - x_start_px
                py2 = rect.bottom() + v_val - current_y_px
                
                pt_x1 = (px1 / self.zoomFactor()) * (72.0 / dpi_x)
                pt_y1 = (py1 / self.zoomFactor()) * (72.0 / dpi_y)
                pt_x2 = (px2 / self.zoomFactor()) * (72.0 / dpi_x)
                pt_y2 = (py2 / self.zoomFactor()) * (72.0 / dpi_y)
                
                start_x, end_x = min(pt_x1, pt_x2), max(pt_x1, pt_x2)
                start_y, end_y = min(pt_y1, pt_y2), max(pt_y1, pt_y2)

                self.selection_page_idx = i
                self.selection_pdf_rect = QRectF(start_x, start_y, end_x - start_x, end_y - start_y)
                
                #wyodrebnianie tekstu
                collected_lines = []
                current_scan_y = start_y
                while current_scan_y <= end_y:
                    pt_start = QPointF(max(0, start_x), current_scan_y)
                    pt_end = QPointF(min(size_pt.width(), end_x), current_scan_y)
                    selection = doc.getSelection(i, pt_start, pt_end)
                    
                    if selection and selection.text():
                        chunk = selection.text().strip()
                        if chunk and (not collected_lines or collected_lines[-1] != chunk):
                            collected_lines.append(chunk)
                    current_scan_y += 4.0 
                
                self.selected_text = " ".join(collected_lines)
                self.update_selection_box_pos()
                break
            current_y_px += page_h_px + self.pageSpacing()

    #menu na prawy przycisk myszy
    def show_context_menu(self, global_pos):
        menu = QMenu(self)
        copy_action = QAction("Skopiuj tekst", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        
        plagiat_action = QAction("Sprawdź plagiat", self)
        plagiat_action.triggered.connect(self.check_plagiarism) 
        
        menu.addAction(copy_action)
        menu.addAction(plagiat_action)
        menu.exec(global_pos)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.selected_text)

    def check_plagiarism(self):
        if not self.selected_text:
            # Możesz wysłać sygnał do statusbaru w main_window
            return
            
        # Usunięcie zbędnych białych znaków
        clean_text = " ".join(self.selected_text.split())
        
        # limit maksymalnie 300 znaków
        if len(clean_text) > 300:
            clean_text = clean_text[:300]
            print("Ostrzeżenie: Przekroczono limit 300 znaków. Tekst został przycięty.")

        encoded_phrase = quote_plus(f'"{clean_text}"')
        webbrowser.open(f"https://www.google.com/search?q={encoded_phrase}")
