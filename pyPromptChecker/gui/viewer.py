# -*- coding: utf-8 -*-

from .dialog import PixmapLabel
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ImageWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen = QApplication.primaryScreen()
        self.filepath = ''
        self.max_screen = self.screen.availableGeometry()
        self.screen_center = self.screen.geometry().center()

    def init_image_window(self):
        label = PixmapLabel()
        pixmap = QPixmap(self.filepath)

        screen_width = int(self.max_screen.width() * 0.95)
        screen_height = int(self.max_screen.height() * 0.95)
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        width = screen_width if pixmap_width > screen_width else pixmap_width
        height = screen_height if pixmap_height > screen_height else pixmap_height

        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        title = 'Image: ' + str(pixmap.width()) + 'x' + str(pixmap.height())
        self.setWindowTitle(title)

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.clicked.connect(self.clicked)

        self.setCentralWidget(label)
        visible = self.isVisible()
        self.show()
        self.adjustSize()

        if not visible:
            self.move_centre()

    def clicked(self):
        self.close()

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
