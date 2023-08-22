# -*- coding: utf-8 -*-

from .dialog import ProgressDialog
from .dialog import PixmapLabel
from functools import lru_cache
from PyQt6.QtWidgets import QMainWindow, QApplication, QGridLayout, QGroupBox, QCheckBox, QScrollArea
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap, QImageReader
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
        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)

        title = 'Image: ' + str(pixmap.width()) + 'x' + str(pixmap.height())
        self.setWindowTitle(title)

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#        label.setScaledContents(True)

        label.clicked.connect(self.clicked)

        self.setCentralWidget(label)

        visible = self.isVisible()

        self.show()

        if not visible:
            move_centre(self)

    def clicked(self):
        self.close()


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Thumbnail View')
        self.filelist_for_return = []
        self.filelist_original = []

    def init_thumbnail(self, filelist):
        self.filelist_original = filelist
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(filelist))
        base_layout = QGridLayout()
        row = col = 0

        for array in filelist:
            filepath, filename, tab_index = array

            portrait_border = QGroupBox()
            portrait_border.setMaximumWidth(190)
            portrait_border.setMinimumWidth(190)

            portrait_layout = QVBoxLayout()
            portrait_border.setLayout(portrait_layout)

            pixmap = portrait_generator(filepath)
            pixmap_label = PixmapLabel()
            pixmap_label.setMinimumSize(150, 150)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setToolTip(filename)
            pixmap_label.setObjectName(filename)
            pixmap_label.clicked.connect(self.pixmap_clicked)

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

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        json_button = QPushButton('Export selected images JSON')
        json_button.clicked.connect(self.json_button_clicked)
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close_button_clicked)
        button_layout.addWidget(json_button)
        button_layout.addWidget(close_button)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(button_layout)
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        scroll_area.setMinimumWidth(thumb.sizeHint().width() + 18)
        if row > 2:
            scroll_area.setMinimumHeight(portrait_layout.sizeHint().height() * 3)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()
        self.show()
        move_centre(self, self.parent())

    def check_box_changed(self):
        filename = self.sender().objectName()
        self.sender().parent().setStyleSheet("QGroupBox {background-color: #86cecb;}")
        if self.sender().isChecked():
            for array in self.filelist_original:
                if filename == array[1]:
                    self.filelist_for_return.append(array[0])
                    break
        else:
            for array in self.filelist_original:
                self.sender().parent().setStyleSheet("")
                if filename == array[1]:
                    self.filelist_for_return.remove(array[0])

    def pixmap_clicked(self):
        self.parent().activateWindow()
        target_tab = self.sender().objectName()
        self.parent().root_tab_change(target_tab)

    def json_button_clicked(self):
        index_list = []
        for filepath in self.filelist_for_return:
            for array in self.filelist_original:
                if filepath == array[0]:
                    index_list.append(array[2])
                    break
        self.parent().export_json_selected(index_list)

    def close_button_clicked(self):
        self.close()


@lru_cache(maxsize=1000)
def portrait_generator(filepath):
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.FastTransformation)
    return pixmap


def move_centre(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())
