import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QFileDialog, QLabel,
                             QVBoxLayout, QWidget, QMessageBox, QToolBar, QScrollArea,
                             QInputDialog, QDialog, QSlider, QHBoxLayout, QPushButton,
                             QToolButton, QMenu, QColorDialog)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, QPoint
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
import matplotlib.pyplot as plt


# Helper: Convert a PIL Image to QPixmap.
def pil2pixmap(im):
    im = im.convert("RGBA")
    data = im.tobytes("raw", "RGBA")
    qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimage)


# Custom QLabel for cropping and freehand drawing.
class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cropping = False
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.crop_rect = None
        self.drawing_lines = []  # Stores finished drawing paths
        self.current_path = []  # Stores current freehand path
        self.crop_callback = None  # Callback when cropping is done
        self.setMouseTracking(True)

    def set_cropping(self, cropping: bool):
        self.cropping = cropping
        if cropping:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def set_drawing(self, drawing: bool):
        self.drawing = drawing
        if drawing:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if self.cropping:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.update()
        elif self.drawing:
            self.current_path = [event.pos()]
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.cropping and self.start_point:
            self.end_point = event.pos()
            self.update()
        elif self.drawing and self.current_path:
            self.current_path.append(event.pos())
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.cropping and self.start_point:
            self.end_point = event.pos()
            self.crop_rect = QRect(self.start_point, self.end_point).normalized()
            self.start_point = None
            self.end_point = None
            self.update()
            if self.crop_callback:
                self.crop_callback(self.crop_rect)
        elif self.drawing and self.current_path:
            self.current_path.append(event.pos())
            self.drawing_lines.append(list(self.current_path))
            self.current_path = []
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # Draw cropping rectangle in red dashed line.
        if self.cropping and self.start_point and self.end_point:
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)
        # Draw freehand drawing in blue (or selected color if drawing mode is on).
        if self.drawing:
            # Note: The drawn lines here are just a preview.
            painter.setPen(QPen(Qt.blue, 2))
            for path in self.drawing_lines:
                if len(path) > 1:
                    for i in range(len(path) - 1):
                        painter.drawLine(path[i], path[i + 1])
            if self.current_path and len(self.current_path) > 1:
                for i in range(len(self.current_path) - 1):
                    painter.drawLine(self.current_path[i], self.current_path[i + 1])


# A simple dialog for color adjustments.
class ColorAdjustDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Adjustments")
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 200)
        self.brightness_slider.setValue(100)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(0, 200)
        self.saturation_slider.setValue(100)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Brightness"))
        layout.addWidget(self.brightness_slider)
        layout.addWidget(QLabel("Contrast"))
        layout.addWidget(self.contrast_slider)
        layout.addWidget(QLabel("Saturation"))
        layout.addWidget(self.saturation_slider)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_values(self):
        return (self.brightness_slider.value() / 100.0,
                self.contrast_slider.value() / 100.0,
                self.saturation_slider.value() / 100.0)


# Main window that integrates all features.
class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced PyQt Image Editor")
        self.setGeometry(100, 100, 1000, 700)

        # The current image is stored as a PIL image.
        self.current_image = None
        self.undo_stack = []  # For undo/redo functionality.
        self.redo_stack = []
        self.zoom_factor = 1.0
        # Drawing parameters:
        self.brush_color = QColor("blue")
        self.brush_size = 3

        # Create toolbar and add action buttons.
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        open_act = QAction("Open", self)
        open_act.triggered.connect(self.open_image)
        toolbar.addAction(open_act)

        save_act = QAction("Save", self)
        save_act.triggered.connect(self.save_image)
        toolbar.addAction(save_act)

        crop_act = QAction("Crop", self)
        crop_act.triggered.connect(self.crop_mode)
        toolbar.addAction(crop_act)

        resize_act = QAction("Resize", self)
        resize_act.triggered.connect(self.resize_image)
        toolbar.addAction(resize_act)

        rotate_act = QAction("Rotate...", self)
        rotate_act.triggered.connect(self.advanced_rotate)
        toolbar.addAction(rotate_act)

        flip_h_act = QAction("Flip H", self)
        flip_h_act.triggered.connect(self.flip_horizontal)
        toolbar.addAction(flip_h_act)

        flip_v_act = QAction("Flip V", self)
        flip_v_act.triggered.connect(self.flip_vertical)
        toolbar.addAction(flip_v_act)

        color_adj_act = QAction("Adjust Colors", self)
        color_adj_act.triggered.connect(self.adjust_colors)
        toolbar.addAction(color_adj_act)

        # Create a QMenu for filters and add it to a QToolButton.
        filters_menu = QMenu("Filters", self)
        grayscale_act = QAction("Grayscale", self)
        grayscale_act.triggered.connect(lambda: self.apply_filter("Grayscale"))
        filters_menu.addAction(grayscale_act)
        sepia_act = QAction("Sepia", self)
        sepia_act.triggered.connect(lambda: self.apply_filter("Sepia"))
        filters_menu.addAction(sepia_act)
        blur_act = QAction("Blur", self)
        blur_act.triggered.connect(lambda: self.apply_filter("Blur"))
        filters_menu.addAction(blur_act)
        sharpen_act = QAction("Sharpen", self)
        sharpen_act.triggered.connect(lambda: self.apply_filter("Sharpen"))
        filters_menu.addAction(sharpen_act)
        edge_act = QAction("Edge Detection", self)
        edge_act.triggered.connect(lambda: self.apply_filter("Edge Detection"))
        filters_menu.addAction(edge_act)
        filters_button = QToolButton()
        filters_button.setText("Filters")
        filters_button.setMenu(filters_menu)
        filters_button.setPopupMode(QToolButton.InstantPopup)
        toolbar.addWidget(filters_button)

        draw_act = QAction("Draw", self)
        draw_act.triggered.connect(self.toggle_drawing)
        toolbar.addAction(draw_act)

        # New actions to choose brush color and adjust brush size.
        brush_color_act = QAction("Brush Color", self)
        brush_color_act.triggered.connect(self.choose_brush_color)
        toolbar.addAction(brush_color_act)

        brush_size_act = QAction("Brush Size", self)
        brush_size_act.triggered.connect(self.set_brush_size)
        toolbar.addAction(brush_size_act)

        undo_act = QAction("Undo", self)
        undo_act.triggered.connect(self.undo)
        toolbar.addAction(undo_act)

        redo_act = QAction("Redo", self)
        redo_act.triggered.connect(self.redo)
        toolbar.addAction(redo_act)

        zoom_in_act = QAction("Zoom In", self)
        zoom_in_act.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_act)

        zoom_out_act = QAction("Zoom Out", self)
        zoom_out_act.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_act)

        hist_act = QAction("Histogram", self)
        hist_act.triggered.connect(self.show_histogram)
        toolbar.addAction(hist_act)

        # Placeholder for layer support.
        layer_act = QAction("Layers", self)
        layer_act.triggered.connect(self.layer_support)
        toolbar.addAction(layer_act)

        # Use a scroll area for zooming and panning.
        self.image_label = ImageLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.crop_callback = self.crop_image  # Callback when crop is finished.
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

    # ---------- Core Functions ----------
    def open_image(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                               "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if fname:
            try:
                self.current_image = Image.open(fname)
                self.undo_stack = [self.current_image.copy()]
                self.redo_stack = []
                self.zoom_factor = 1.0
                self.update_display()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def update_display(self):
        if self.current_image:
            pixmap = pil2pixmap(self.current_image)
            # Apply zoom factor.
            w = int(pixmap.width() * self.zoom_factor)
            h = int(pixmap.height() * self.zoom_factor)
            pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def save_image(self):
        if self.current_image:
            fname, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if fname:
                self.current_image.save(fname)
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def push_undo(self):
        if self.current_image:
            self.undo_stack.append(self.current_image.copy())
            self.redo_stack.clear()

    # ---------- Editing Tools ----------
    def crop_mode(self):
        if self.current_image:
            self.image_label.set_cropping(True)
            QMessageBox.information(self, "Crop", "Drag a rectangle on the image to crop, then release the mouse.")
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def crop_image(self, rect: QRect):
        """Crop the image using the selected rectangle.
           The rect is in widget coordinates so we map it to the image coordinates.
        """
        pixmap = self.image_label.pixmap()
        if not pixmap:
            return
        label_size = self.image_label.size()
        pixmap_size = pixmap.size()
        # Compute offsets if the pixmap is centered.
        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2
        # Adjust the rectangle coordinates relative to the pixmap.
        x = rect.x() - offset_x
        y = rect.y() - offset_y
        if x < 0 or y < 0 or (x + rect.width()) > pixmap_size.width() or (y + rect.height()) > pixmap_size.height():
            QMessageBox.warning(self, "Crop", "Selected area is out of image bounds.")
            self.image_label.set_cropping(False)
            return
        # Map to original image coordinates.
        img_w, img_h = self.current_image.size
        scale_x = img_w / pixmap_size.width()
        scale_y = img_h / pixmap_size.height()
        crop_box = (int(x * scale_x), int(y * scale_y),
                    int((x + rect.width()) * scale_x), int((y + rect.height()) * scale_y))
        self.push_undo()
        self.current_image = self.current_image.crop(crop_box)
        self.update_display()
        self.image_label.set_cropping(False)

    def resize_image(self):
        if self.current_image:
            w, h = self.current_image.size
            new_w, ok = QInputDialog.getInt(self, "Resize", "New width:", value=w, min=1)
            if not ok:
                return
            new_h, ok = QInputDialog.getInt(self, "Resize", "New height:", value=h, min=1)
            if not ok:
                return
            self.push_undo()
            self.current_image = self.current_image.resize((new_w, new_h), Image.ANTIALIAS)
            self.update_display()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def advanced_rotate(self):
        if self.current_image:
            angle, ok = QInputDialog.getDouble(self, "Rotate", "Enter rotation angle (degrees):", decimals=2)
            if not ok:
                return
            self.push_undo()
            # Negative angle rotates clockwise.
            self.current_image = self.current_image.rotate(-angle, expand=True)
            self.update_display()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def flip_horizontal(self):
        if self.current_image:
            self.push_undo()
            self.current_image = ImageOps.mirror(self.current_image)
            self.update_display()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def flip_vertical(self):
        if self.current_image:
            self.push_undo()
            self.current_image = ImageOps.flip(self.current_image)
            self.update_display()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def adjust_colors(self):
        if self.current_image:
            dialog = ColorAdjustDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                brightness, contrast, saturation = dialog.get_values()
                self.push_undo()
                img = self.current_image
                img = ImageEnhance.Brightness(img).enhance(brightness)
                img = ImageEnhance.Contrast(img).enhance(contrast)
                img = ImageEnhance.Color(img).enhance(saturation)
                self.current_image = img
                self.update_display()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def apply_filter(self, filter_name):
        if not self.current_image:
            QMessageBox.warning(self, "Warning", "No image loaded.")
            return
        self.push_undo()
        img = self.current_image
        if filter_name == "Grayscale":
            img = img.convert("L").convert("RGB")
        elif filter_name == "Sepia":
            # A simple sepia filter.
            sepia = []
            for i in range(255):
                sepia.append((int(i * 240 / 255), int(i * 200 / 255), int(i * 145 / 255)))
            img = img.convert("L")
            img = img.point(lambda p: sepia[p])
        elif filter_name == "Blur":
            img = img.filter(ImageFilter.BLUR)
        elif filter_name == "Sharpen":
            img = img.filter(ImageFilter.SHARPEN)
        elif filter_name == "Edge Detection":
            img = img.filter(ImageFilter.FIND_EDGES)
        self.current_image = img
        self.update_display()

    # ---------- Drawing and Annotation ----------
    def toggle_drawing(self):
        if self.current_image:
            # Toggle drawing mode.
            self.image_label.set_drawing(not self.image_label.drawing)
            # When turning drawing off, apply the drawn paths.
            if not self.image_label.drawing:
                self.apply_drawing()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    def apply_drawing(self):
        if not self.current_image or not self.image_label.drawing_lines:
            return
        pixmap = self.image_label.pixmap()
        if not pixmap:
            return
        label_size = self.image_label.size()
        pixmap_size = pixmap.size()
        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2
        draw = ImageDraw.Draw(self.current_image)
        img_w, img_h = self.current_image.size
        scale_x = img_w / pixmap_size.width()
        scale_y = img_h / pixmap_size.height()
        for path in self.image_label.drawing_lines:
            if len(path) > 1:
                converted = []
                for point in path:
                    x = (point.x() - offset_x) * scale_x
                    y = (point.y() - offset_y) * scale_y
                    converted.append((x, y))
                draw.line(converted, fill=self.brush_color.name(), width=self.brush_size)
        self.image_label.drawing_lines.clear()
        self.update_display()

    # New methods to choose brush color and brush size.
    def choose_brush_color(self):
        color = QColorDialog.getColor(initial=self.brush_color, title="Select Brush Color", parent=self)
        if color.isValid():
            self.brush_color = color

    def set_brush_size(self):
        size, ok = QInputDialog.getInt(self, "Brush Size", "Enter brush size:", value=self.brush_size, min=1, max=100)
        if ok:
            self.brush_size = size

    # ---------- Undo / Redo ----------
    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.current_image = self.undo_stack[-1].copy()
            self.update_display()
        else:
            QMessageBox.information(self, "Undo", "No more actions to undo.")

    def redo(self):
        if self.redo_stack:
            self.current_image = self.redo_stack.pop().copy()
            self.undo_stack.append(self.current_image.copy())
            self.update_display()
        else:
            QMessageBox.information(self, "Redo", "No actions to redo.")

    # ---------- Zoom and Pan ----------
    def zoom_in(self):
        self.zoom_factor *= 1.25
        self.update_display()

    def zoom_out(self):
        self.zoom_factor /= 1.25
        self.update_display()

    # ---------- Histogram and Analysis ----------
    def show_histogram(self):
        if self.current_image:
            hist = self.current_image.histogram()
            # Assume RGB image; split histogram for R, G, B.
            r = hist[0:256]
            g = hist[256:512]
            b = hist[512:768]
            plt.figure("Histogram")
            plt.subplot(3, 1, 1)
            plt.plot(r, color="red")
            plt.subplot(3, 1, 2)
            plt.plot(g, color="green")
            plt.subplot(3, 1, 3)
            plt.plot(b, color="blue")
            plt.tight_layout()
            plt.show()
        else:
            QMessageBox.warning(self, "Warning", "No image loaded.")

    # ---------- Layers (Stub) ----------
    def layer_support(self):
        QMessageBox.information(self, "Layer Support", "Layer support is not implemented in this demo.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEditor()
    window.show()
    sys.exit(app.exec_())