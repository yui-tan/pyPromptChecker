# -*- coding: utf-8 -*-

from .widget import *
from .dialog import *
from .custom import *
from .menu import ThumbnailMenu
from .viewer import DiffWindow
from . import config

import os
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QPushButton


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size = config.get('ThumbnailPixmapSize', 150)
        self.setWindowTitle('Thumbnail View')
        self.params = []
        self.selected = set()
        self.total_images = 0
        self.menu = ThumbnailMenu(self)
        make_keybindings(self)

    def init_thumbnail(self, param_list: dict):
        self.setCentralWidget(None)
        self.params = param_list
        self.total_images = len(param_list)
        portrait_border = 0

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, self.total_images)

        thumbnails_layout = QGridLayout()
        row = 0
        col = 0
        width = 0
        real_row = 0

        for index, param in enumerate(param_list):
            real_row = row
            filepath = param.get('Filepath')
            portrait_border = ThumbnailBorder(index, filepath, self.size)
            portrait_border.clicked.connect(self._group_clicked)
            portrait_border.pixmap_label.rightClicked.connect(self._pixmap_clicked)
            thumbnails_layout.addWidget(portrait_border, row, col)

            width += (self.size + 40)
            col += 1

            if width > 900:
                col = width = 0
                row += 1

            progress.update_value()

        thumbnails = QWidget()
        thumbnails.setLayout(thumbnails_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(thumbnails)

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self._footer_buttons())
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        scroll_area.setMinimumWidth(thumbnails.sizeHint().width() + 25)
        estimated_height = portrait_border.sizeHint().height()

        if real_row == 0:
            estimated_height = min(estimated_height + 70, 1000)
        elif real_row == 1:
            estimated_height = min(estimated_height * 2 + 70, 1000)
        elif real_row > 1:
            estimated_height = min(estimated_height * 3 + 70, 1000)

        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()

        self.show()
        self.resize(900, estimated_height)
        self._move_centre()

    def _footer_buttons(self):
        management = config.get('MoveDelete', False)
        button_layout = QHBoxLayout()

        for button_text in ('Select all', 'Export JSON', 'Diff', 'Interrogate', 'Close'):
            button = QPushButton(button_text)
            button.setObjectName(button_text)
            button.clicked.connect(self._footer_button_clicked)
            button_layout.addWidget(button)

            if button_text == 'Interrogate' and management:
                management_button = ButtonWithMenu()
                management_button.setText('Add favourite')
                management_button.setObjectName('Add favourite')
                management_button.clicked.connect(self._footer_button_clicked)
                management_button.rightClicked.connect(self._footer_submenu)
                button_layout.addWidget(management_button)

        return button_layout

    def _footer_button_clicked(self):
        where_from = self.sender().objectName()
        selected_number = len(self.selected)
        if selected_number > 0:
            if where_from == 'Add favourite':
                self.management_image('favourite')

            elif where_from == 'Export JSON':
                self.parent().export_json_selected(list(self.selected))

            elif where_from == 'Interrogate':
                self.parent().add_interrogate_tab(2, self.selected)

            elif where_from == 'Diff':
                if selected_number == 2:
                    result = [self.params[i] for i in self.selected]
                    diff = DiffWindow(result, self)
                    diff.show()
                    diff.move_centre()

        if where_from == 'Close':
            self.close()

        elif where_from == 'Select all':
            if selected_number == self.total_images:
                self._select_all(True)
            else:
                self._select_all(False)

    def _footer_submenu(self):
        x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
        y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.menu.sizeHint().height()
        adjusted_pos = QPoint(x, y)
        self.menu.exec(adjusted_pos)

    def _select_all(self, clear: bool):
        for widget in self.centralWidget().findChildren(ThumbnailBorder):
            if clear and widget.selected:
                widget.self_clicked()
                self.selected.discard(widget.index)
            elif not clear and not widget.selected:
                widget.self_clicked()
                self.selected.add(widget.index)

    def _group_clicked(self):
        group = self.sender().objectName()
        str_number = group.split('_')[1]
        number = int(str_number)

        if self.sender().selected:
            self.selected.add(number)
        else:
            self.selected.discard(number)

    def _pixmap_clicked(self):
        pixmap = self.sender().objectName()
        str_number = pixmap.split('_')[1]
        number = int(str_number)
        self.parent().root_tab.setCurrentIndex(number)
        self.parent().pixmap_clicked()

    def _move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()

        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def management_image(self, kind: str):
        border_str = 'deleted' if kind == 'delete' else 'moved'
        success, error = self.parent().manage_image_files(list(self.selected), self, kind)

        if not success and not error:
            return

        if success:
            target = [[value[0], value[1]] for value in success if value[0] in self.selected]
            for index, filepath in target:
                widget = self.centralWidget().findChild(ThumbnailBorder, f'group_{index}')
                widget.self_clicked()
                widget.label_border(border_str)
                widget.label_change(filepath)
            self.selected.clear()

        if error:
            text = '\n'.join(error)
            MessageBox(text, 'Error', 'ok', 'critical', self)


class ThumbnailBorder(ClickableGroup):
    def __init__(self, index, filepath, size=150, parent=None):
        super().__init__(parent)
        self.size = size
        self.index = index
        self.label = None
        self.pixmap_label = None
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.selected = False
        self._init_class()

        self.setObjectName(f'group_{self.index}')
        self.clicked.connect(self.self_clicked)

    def _init_class(self):
        self.layout = QVBoxLayout()
        self.setFixedSize(self.size + 60, self.size + 60)

        label = self._filename_label()
        pixmap = self._pixmap_label()
        self.label = label
        self.pixmap_label = pixmap

        self.layout.addWidget(pixmap, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.setLayout(self.layout)

    def _pixmap_label(self):
        pixmap = portrait_generator(self.filepath, self.size)
        pixmap_label = PixmapLabel()
        pixmap_label.setFixedSize(self.size, self.size)
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        pixmap_label.setToolTip(self.filename)
        pixmap_label.setObjectName(f'pixmap_{self.index}')
        return pixmap_label

    def _filename_label(self):
        label = HoverLabel()
        label.setText(self.filename)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(30)
        return label

    def self_clicked(self):
        if self.selected:
            self.selected = False
            self.setStyleSheet('')
        else:
            self.selected = True
            self.setStyleSheet(custom_stylesheet('groupbox', 'current'))

    def label_border(self, what_happen: str):
        if what_happen == 'moved':
            self.pixmap_label.setStyleSheet(custom_stylesheet('border', what_happen))
        elif what_happen == 'deleted':
            self.pixmap_label.setStyleSheet(custom_stylesheet('border', what_happen))

    def label_change(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.label.setText(self.filename)
        self.pixmap_label.setToolTip(self.filename)
