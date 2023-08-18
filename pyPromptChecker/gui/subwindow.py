# -*- coding: utf-8 -*-

import os
from .dialog import ProgressDialog
from .dialog import PixmapLabel
from functools import lru_cache
from PyQt6.QtWidgets import QMainWindow, QApplication, QGridLayout, QGroupBox, QCheckBox, QScrollArea
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt


class ImageWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen = QApplication.primaryScreen()
        self.filepath = ''
        self.max_screen = self.screen.availableGeometry()
        self.screen_center = self.screen.geometry().center()

    def init_ui(self):
        label = PixmapLabel()
        pixmap = QPixmap(self.filepath)

        screen_width = int(self.max_screen.width() * 0.95)
        screen_height = int(self.max_screen.height() * 0.95)
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()
        width = screen_width if pixmap_width > screen_width else pixmap_width
        height = screen_height if pixmap_height > screen_height else pixmap_height
        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)

        title = 'Image: ' + str(pixmap.width()) + 'x' + str(pixmap.height())
        self.setWindowTitle(title)

        label.setPixmap(pixmap)
        label.setScaledContents(True)

        label.clicked.connect(self.clicked)

        self.setCentralWidget(label)
        self.show()
        move_center(self)

    def clicked(self):
        self.close()


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle('Thumbnail View')
        self.file_list = []

    def init_ui(self, filelist):
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(filelist))
        base_layout = QGridLayout()
        row = col = 0

        for filepath in filelist:
            filename = os.path.basename(filepath)

            portrait_border = QGroupBox()
            portrait_border.setMaximumWidth(190)
            portrait_border.setMinimumWidth(190)

            portrait_layout = QVBoxLayout()
            portrait_border.setLayout(portrait_layout)

            pixmap = portrait_generator(filepath)
            pixmap_label = QLabel()
            pixmap_label.setMinimumSize(150, 150)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setToolTip(filename)

            check_box = QCheckBox(filename)
            check_box.setObjectName(filename)
            check_box.stateChanged.connect(self.check_box_changed)

            portrait_layout.addWidget(pixmap_label)
            portrait_layout.addWidget(check_box)
            base_layout.addWidget(portrait_border, row, col)

            col = col + 1
            if col == 5:
                col = 0
                row = row + 1

            progress.update_value()

        thumb = QWidget()
        thumb.setLayout(base_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(thumb)

        self.setCentralWidget(scroll_area)

        scroll_area.setMinimumWidth(thumb.sizeHint().width() + 16)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()
        self.show()

    def check_box_changed(self):
        filename = self.sender().objectName()
        if self.sender().isChecked():
            print('"{}" checked !'.format(filename))
        else:
            print('"{}" unchecked !'.format(filename))


@lru_cache(maxsize=None)
def portrait_generator(filepath):
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.FastTransformation)
    return pixmap


def move_center(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())
