# -*- coding: utf-8 -*-

from .dialog import PixmapLabel
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QScrollArea, QLabel
from PyQt6.QtWidgets import QTextEdit
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


class DiffWindow(QMainWindow):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params
        self.setWindowTitle('Diff Window')
        self.init_diff()

    def init_diff(self):
        central_widget = QWidget()
        central_widget_layout = QHBoxLayout()

        for i in range(2):
            status = QWidget()
            status_layout = QGridLayout()

            pixmap_label = PixmapLabel()
            pixmap = QPixmap(self.params[i].get('Filepath'))
            pixmap = pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setFixedSize(350, 350)

            status_layout.addWidget(pixmap_label, 0, i)

            j = 0
            scroll = QScrollArea()
            scroll_area = QWidget()
            scroll_layout = QGridLayout()

            for key, item in self.params[i].items():
                if key == 'Positive' or key == 'Negative':
                    textbox = QTextEdit()
                    text = item.replace('\n', '<BR>')
                    textbox.setHtml(text)
                    if key == 'Positive':
                        status_layout.addWidget(textbox, 2, i)
                        continue
                    else:
                        status_layout.addWidget(textbox, 3, i)
                        continue
                title = QLabel(key)
                value = QLabel(item)
                scroll_layout.addWidget(title, j, 0)
                scroll_layout.addWidget(value, j, 1)
                j += 1

            scroll_area.setLayout(scroll_layout)
            scroll.setWidget(scroll_area)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            status_layout.addWidget(scroll, 1, i)
            status.setLayout(status_layout)
            central_widget_layout.addWidget(status)

        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)


def status_index():
    status = ['Extensions',
              'Filepath',
              'Timestamp',
              'Image size',
              'Size',
              'Seed',
              'Sampler',
              'Eta',
              'Steps',
              'CFG scale',
              'Model',
              'VAE',
              'Variation seed',
              'Variation seed strength',
              'Seed resize from',
              'Denoising strength',
              'Clip skip',
              'Lora',
              'Textual inversion',
              'ENSD',
              'Version'
              ]