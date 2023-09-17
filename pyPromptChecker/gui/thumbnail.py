# -*- coding: utf-8 -*-

from . import config
from .dialog import ProgressDialog
from .dialog import PixmapLabel
from .viewer import DiffWindow
from .widget import portrait_generator
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea
from PyQt6.QtWidgets import QWidget, QPushButton, QCheckBox


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size = config.get('ThumbnailPixmapSize', 150)
        self.setWindowTitle('Thumbnail View')
        self.params = []

    def init_thumbnail(self, param_list):
        self.setCentralWidget(None)
        self.params = param_list

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(param_list))

        base_layout = QGridLayout()
        row = col = width = 0

        for index, param in enumerate(param_list):
            filepath = param.get('Filepath')
            filename = param.get('Filename')

            portrait_border = QGroupBox()
            portrait_layout = QVBoxLayout()
            portrait_border.setMaximumWidth(self.size + 40)
            portrait_border.setMinimumWidth(self.size + 40)
            portrait_border.setLayout(portrait_layout)

            pixmap = portrait_generator(filepath, self.size)
            pixmap_label = PixmapLabel()
            pixmap_label.setMinimumSize(self.size, self.size)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setToolTip(filename)
            pixmap_label.setObjectName(str(index))
            pixmap_label.clicked.connect(self.pixmap_clicked)

            check_box = QCheckBox(filename)
            check_box.setObjectName(str(index))
            check_box.toggled.connect(self.check_box_changed)

            portrait_layout.addWidget(pixmap_label)
            portrait_layout.addWidget(check_box)
            base_layout.addWidget(portrait_border, row, col)

            width += (self.size + 40)
            col += 1

            if width > 900:
                col = width = 0
                row = row + 1

            progress.update_value()

        thumbnails = QWidget()
        thumbnails.setLayout(base_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(thumbnails)

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        json_button = QPushButton('Export selected images JSON')
        json_button.clicked.connect(self.json_button_clicked)
        button_layout.addWidget(json_button)

        diff_button = QPushButton('Diff')
        diff_button.clicked.connect(self.diff_button_clicked)
        button_layout.addWidget(diff_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close_button_clicked)
        button_layout.addWidget(close_button)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(button_layout)
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        scroll_area.setMinimumWidth(thumbnails.sizeHint().width() + 25)

        estimated_height = portrait_layout.sizeHint().height()

        if row > 2:
            if estimated_height < 300:
                scroll_area.setMinimumHeight(estimated_height * 3)
            else:
                scroll_area.setMaximumHeight(estimated_height + 25)

        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()

        self.show()
        self.move_centre()

    def check_box_changed(self):
        if self.sender().isChecked():
            self.sender().parent().setStyleSheet("QGroupBox {border: 2px solid #86cecb; padding : 1px 0 0 0; }")
        else:
            self.sender().parent().setStyleSheet("")

    def pixmap_clicked(self):
        target_tab = self.sender().objectName()
        self.parent().root_tab.setCurrentIndex(int(target_tab))
        self.parent().activateWindow()

    def json_button_clicked(self):
        indexes = []
        for widget in self.centralWidget().findChildren(QCheckBox):
            if widget.isChecked():
                index = widget.objectName()
                indexes.append(int(index))
        if indexes:
            self.parent().export_json_selected(indexes)

    def diff_button_clicked(self):
        indexes = []
        for widget in self.centralWidget().findChildren(QCheckBox):
            if widget.isChecked():
                index = widget.objectName()
                indexes.append(int(index))
        if len(indexes) == 2:
            result = [self.params[i] for i in indexes]
            diff = DiffWindow(result, self)
            diff.show()
            diff.move_centre()

    def close_button_clicked(self):
        self.close()

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
