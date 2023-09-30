# -*- coding: utf-8 -*-

from .widget import *
from .dialog import *
from .custom import *
from .menu import ThumbnailMenu
from .viewer import DiffWindow
from . import config

import os
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QPushButton


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Thumbnail View')
        self.borders = []
        self.menu = ThumbnailMenu(self)
        make_keybindings(self)

    def init_thumbnail(self, param_list: list, moved: set = None, deleted: set = None):
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(param_list))

        self.setCentralWidget(None)

        row = 0
        col = 0
        width = 0
        real_row = 0
        estimated_height = 0

        size = config.get('ThumbnailPixmapSize', 150)
        thumbnails_layout = QGridLayout()

        for index, param in enumerate(param_list):
            real_row = row
            portrait_border = ThumbnailBorder(index, param, size)
            portrait_border.pixmap_label.rightClicked.connect(self._pixmap_clicked)
            self.borders.append(portrait_border)
            estimated_height = portrait_border.sizeHint().height()
            thumbnails_layout.addWidget(portrait_border, row, col)

            if moved and index in moved:
                portrait_border.set_moved()

            if deleted and index in deleted:
                portrait_border.set_deleted()

            width += (size + 40)
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

        scroll_area.setMinimumWidth(thumbnails.sizeHint().width() + 25)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self._footer_buttons())
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        if real_row == 0:
            estimated_height = min(estimated_height + 70, 1000)
        elif real_row == 1:
            estimated_height = min(estimated_height * 2 + 70, 1000)
        elif real_row > 1:
            estimated_height = min(estimated_height * 3 + 70, 1000)

        self.show()
        self.resize(900, estimated_height)
        move_centre(self)

        progress.close()

    def _footer_buttons(self):
        button_layout = QHBoxLayout()
        management = config.get('MoveDelete', False)
        buttons = ('Select all', 'Export JSON', 'Diff', 'Interrogate', 'Close')
        if management:
            buttons = ('Select all', 'Export JSON', 'Diff', 'Interrogate', 'Add favourite', 'Close')

        for button_text in buttons:
            button = QPushButton() if button_text != 'Add favourite' else ButtonWithMenu()
            button.setText(button_text)
            button.setObjectName(button_text)
            button_layout.addWidget(button)

            button.clicked.connect(self._footer_button_clicked)
            if button_text == 'Add favourite':
                button.rightClicked.connect(self._footer_submenu)

        return button_layout

    def _footer_button_clicked(self):
        where_from = self.sender().objectName()
        selected_index = set()
        window = self.parent()

        for border in self.borders:
            if border.selected:
                selected_index.add(border.index)

        if len(selected_index) > 0:
            if where_from == 'Add favourite':
                self.management_image('favourite')

            elif where_from == 'Export JSON':
                if hasattr(window, 'export_json_selected'):
                    self.parent().export_json_selected(selected_index)

            elif where_from == 'Interrogate':
                if hasattr(window, 'add_interrogate_tab'):
                    self.parent().add_interrogate_tab(2, selected_index)

            elif where_from == 'Diff':
                if len(selected_index) == 2:
                    result = [self.borders[i].params for i in selected_index]
                    diff = DiffWindow(result, self)
                    move_centre(diff)

        if where_from == 'Close':
            self.close()

        elif where_from == 'Select all':
            if len(selected_index) == len(self.borders):
                for border in self.borders:
                    border.set_deselected()
            else:
                for border in self.borders:
                    border.set_selected()

    def _footer_submenu(self):
        x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
        y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.menu.sizeHint().height()
        adjusted_pos = QPoint(x, y)
        self.menu.exec(adjusted_pos)

    def _pixmap_clicked(self):
        if hasattr(self.parent(), 'root_tab'):
            number = self.sender().parent().index
            self.parent().root_tab.setCurrentIndex(number)
            self.parent().pixmap_clicked()

    def management_image(self, kind: str):
        selected = set()

        for border in self.borders:
            if border.selected:
                selected.add(border.index)

        success, error = self.parent().manage_image_files(selected, self, kind)

        if not success and not error:
            return

        if success:
            deselect_target = [[value[0], value[1]] for value in success if value[0] in selected]
            for index, filepath in deselect_target:
                widget = self.borders[index]
                widget.set_deselected()
                widget.label_change(filepath)

                if kind == 'delete':
                    widget.set_deleted()
                else:
                    widget.set_moved()

        if error:
            text = '\n'.join(error)
            MessageBox(text, 'Error', 'ok', 'critical', self)


class ThumbnailBorder(ClickableGroup):
    def __init__(self, index: int, params: dict, size: int = 150, parent=None):
        super().__init__(parent)
        self.size = size
        self.index = index
        self.params = params
        self.label = None
        self.pixmap_label = None
        self.selected = False
        self.moved = False
        self.deleted = False
        self._init_class()

        self.setObjectName(f'group_{self.index}')
        self.clicked.connect(self._toggle_selected)

    def _init_class(self):
        layout = QVBoxLayout()
        self.setFixedSize(self.size + 60, self.size + 60)

        self._pixmap_label()
        self._filename_label()

        filename = self.params.get('Filename')
        self.pixmap_label.setToolTip(self._tooltip())
        self.label.setText(filename)

        layout.addWidget(self.pixmap_label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)

    def _pixmap_label(self):
        filepath = self.params.get('Filepath')
        pixmap = portrait_generator(filepath, self.size)
        pixmap_label = PixmapLabel()
        pixmap_label.setFixedSize(self.size, self.size)
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        pixmap_label.setObjectName(f'pixmap_{self.index}')
        self.pixmap_label = pixmap_label

    def _tooltip(self):
        result = ''
        for key in ('Filename', 'Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version'):
            status = self.params.get(key, 'None')
            result += f'{key} : {status}\n'
        result = result.rstrip('\n')
        return result

    def _filename_label(self):
        label = HoverLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(30)
        self.label = label

    def _toggle_selected(self):
        if self.selected:
            self.set_deselected()
        else:
            self.set_selected()

    def set_selected(self):
        self.selected = True
        self.setStyleSheet(custom_stylesheet('groupbox', 'current'))

    def set_deselected(self):
        self.selected = False
        self.setStyleSheet('')

    def set_moved(self):
        self.label.setStyleSheet(custom_stylesheet('colour', 'moved'))
        self.moved = True
        self.deleted = False

    def set_deleted(self):
        self.label.setStyleSheet(custom_stylesheet('colour', 'deleted'))
        self.moved = False
        self.deleted = True

    def label_change(self, filepath: str):
        current_filepath = self.params.get('Filepath')
        if filepath != current_filepath:
            filename = os.path.basename(filepath)
            self.params['Filepath'] = filepath
            self.params['Filename'] = filename
            self.label.setText(filename)
            self.pixmap_label.setToolTip(self._tooltip())
