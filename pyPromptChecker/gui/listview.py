# -*- coding: utf-8 -*-

from .widget import *
from .dialog import *
from .custom import *
from .menu import ThumbnailMenu
from .viewer import DiffWindow
from . import config

import os
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QComboBox, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPoint


class Listview(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Listview')
        self.borders = []
        self.menu = ThumbnailMenu(self)
        custom_keybindings(self)

    def init_listview(self, param_list: list, moved: set = None, deleted: set = None):
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(param_list))

        self.setCentralWidget(None)

        estimated_height = 0
        size = config.get('ListViewPixmapSize', 200)

        root_widget = QWidget()
        root_layout = QVBoxLayout()

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        scroll_area = QScrollArea()

        for index, param in enumerate(param_list):
            listview_border = ListviewBorder(index, param, size, self)
            estimated_height += (listview_border.sizeHint().height() + 50)
            root_layout.addWidget(listview_border)
            self.borders.append(listview_border)

            if moved and index in moved:
                listview_border.set_moved()

            if deleted and index in deleted:
                listview_border.set_deleted()

            progress.update_value()

        root_widget.setLayout(root_layout)

        estimated_width = root_widget.sizeHint().width() + 50
        estimated_height = 800 if estimated_height > 800 else estimated_height

        scroll_area.setWidget(root_widget)
        scroll_area.setMinimumWidth(estimated_width)
        scroll_area.setMinimumHeight(estimated_height)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        central_widget_layout.addLayout(self._header_section())
        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self._footer_section())

        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        self.show()
        self.resize(estimated_width, estimated_height)
        move_centre(self)

    def _header_section(self):
        row = 1
        col = 0
        header_layout = QGridLayout()
        header_label = QLabel('Status')
        combo_items = ['Timestamp',
                       'Size',
                       'Seed',
                       'Sampler',
                       'Eta',
                       'Steps',
                       'CFG scale',
                       'Model',
                       'VAE',
                       'Var. seed',
                       'Var. strength',
                       'Resize from',
                       'Denoising',
                       'Clip skip',
                       'ENSD',
                       'Version'
                       ]

        header_label.setMinimumWidth(50)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header_label, 0, 0, 1, 4)

        for index, status in enumerate(('Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version')):
            combo_box = QComboBox()
            combo_box.setObjectName(f'status_{index}')
            combo_box.currentIndexChanged.connect(self._status_changed)
            header_layout.addWidget(combo_box, row, col)
            combo_box.addItems(combo_items)
            combo_box.setCurrentText(status)
            col += 1
            if col == 4:
                row += 1
                col = 0

        return header_layout

    def _footer_section(self):
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

    def _status_changed(self):
        if self.centralWidget():
            status_number = self.sender().objectName().split('_')[1]
            status_str = self.sender().currentText()

            if status_str == 'Var. seed':
                search_str = 'Variation seed'
            elif status_str == 'Var. strength':
                search_str = 'Variation seed strength'
            elif status_str == 'Resize from':
                search_str = 'Seed resize from'
            elif status_str == 'Denoising':
                search_str = 'Denoising strength'
            else:
                search_str = status_str

            for index, border in enumerate(self.borders):
                value = border.params.get(search_str, 'None')
                title_label = border.findChild(QLabel, status_number + '_title')
                value_label = border.findChild(QLabel, status_number + '_value')

                title_label.setText(status_str)
                value_label.setText(value)

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

    def management_image(self, kind: str):
        selected = set()

        for border in self.borders:
            if border.selected:
                selected.add(border.index)

        if hasattr(self.parent(), 'manage_image_files'):
            success, error = self.parent().manage_image_files(selected, self, kind)
        else:
            success, error = None, 'An unexpected error has occurred.'

        if not success and not error:
            return

        if success:
            deselect_target = [[value[0], value[1]] for value in success if value[0] in selected]
            for index, filepath in deselect_target:
                widget = self.borders[index]
                widget.set_deselected()
                widget.title_change(filepath)

                if kind == 'delete':
                    widget.set_deleted()
                else:
                    widget.set_moved()

        if error:
            text = '\n'.join(error)
            MessageBox(text, 'Error', 'ok', 'critical', self)


class ListviewBorder(ClickableGroup):
    def __init__(self, index: int, params: dict, size: int = 200, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.size = size
        self.index = index
        self.params = params
        self.pixmap_label = None
        self.status_labels = []
        self.selected = False
        self.moved = False
        self.deleted = False
        self.changed = 0
        self.status = ['Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version']
        self._init_class()

        self.setObjectName(f'group_{index}')
        self.clicked.connect(self._toggle_selected)

    def _init_class(self):
        layout = QHBoxLayout()

        layout.addWidget(self._pixmap_label())
        layout.addLayout(self._status_labels())
        layout.addLayout(self._extension_labels())

        self.setLayout(layout)
        self.setTitle(self.params.get('Filepath', 'None'))

    def _pixmap_label(self):
        filepath = self.params.get('Filepath')
        pixmap = portrait_generator(filepath, self.size)
        pixmap_label = PixmapLabel()
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setFixedSize(self.size, self.size)
        pixmap_label.clicked.connect(self._toggle_selected)
        pixmap_label.rightClicked.connect(self._toggle_selected)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap_label.setObjectName(f'pixmap_{self.index}')
        return pixmap_label

    def _status_labels(self):
        status_layout = QGridLayout()
        status_layout.setColumnMinimumWidth(0, 20)
        status_layout.setColumnMinimumWidth(0, 20)

        for index, key in enumerate(self.status):
            item = self.params.get(key, 'None')

            title_label = QLabel(key)
            title_label.setObjectName(f'{index}_title')
            status_label = QLabel(item)
            status_label.setObjectName(f'{index}_value')

            title_label.setFixedSize(100, 20)
            status_label.setFixedHeight(20)
            status_label.setMinimumWidth(200)

            status_layout.addWidget(title_label, index, 1)
            status_layout.addWidget(status_label, index, 3)

        return status_layout

    def _extension_labels(self):
        j = 0
        k = 0
        extension_layout = QGridLayout()

        creation = 'txt2img'
        if any(key in v for v in self.params for key in ('Upscaler', 'Extras')):
            creation = 'img2img'
        if self.params.get('Positive') == 'This file has no embedded data':
            creation = '---'
        if 'Mask blur' in self.params:
            creation = 'inpaint'

        addnet = any(key in v for v in self.params for key in ('Lora', 'Textual inversion', 'Add network'))
        cfg = any(key in v for v in self.params for key in ('Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler'))

        for condition_list in [
            [self.params.get('Extensions', '---'), 'extension'],
            [creation, 'creation'],
            ['Extras', 'Extras' in self.params],
            ['Variation', 'Variation seed' in self.params],
            ['Hires.fix', 'Hires upscaler' in self.params],
            ['Lora/AddNet', addnet],
            ['CFG', cfg],
            ['Tiled Diffusion', 'Tiled diffusion' in self.params],
            ['ControlNet', 'ControlNet' in self.params],
            ['Regional', 'RP Active' in self.params]
        ]:

            title, status = condition_list

            extension_label = QLabel(title)
            extension_label.setFixedWidth(100)
            extension_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if not status or title == '---':
                extension_label.setDisabled(True)
                extension_label.setStyleSheet(custom_stylesheet('extension_label_disable', 'disabled'))

            elif status == 'extension' and title != '---':
                extension_label.setStyleSheet(custom_stylesheet('extension_label', title))

            elif status == 'creation' and title != '---':
                extension_label.setStyleSheet(custom_stylesheet('extension_label', title))

            else:
                extension_label.setStyleSheet(custom_stylesheet('extension_label', 'available'))

            extension_layout.addWidget(extension_label, j, k)

            if j == 4:
                k += 1
                j = 0
            else:
                j += 1

        return extension_layout

    def _toggle_selected(self):
        if self.parent_window.isActiveWindow():
            if 'group' in self.sender().objectName() and self.changed == 0:
                if self.selected:
                    self.set_deselected()
                else:
                    self.set_selected()
                self.changed = 1

            elif 'pixmap' in self.sender().objectName() and self.changed == 0:
                if hasattr(self.parent_window.parent(), 'root_tab'):
                    self.parent_window.parent().root_tab.setCurrentIndex(self.index)
                    self.parent_window.parent().pixmap_clicked()
                self.changed = 1

            self.timer = QTimer()
            self.timer.timeout.connect(self._initialize_changed)
            self.timer.start(10)

    def _initialize_changed(self):
        self.changed = 0
        self.timer.stop()

    def _pixmap_clicked(self):
        if hasattr(self.parent_window.parent(), 'root_tab'):
            self.parent_window.parent().root_tab.setCurrentIndex(self.index)
            self.parent_window.parent().pixmap_clicked()

    def set_selected(self):
        current_stylesheet = self.styleSheet()
        current_stylesheet = custom_stylesheet('groupbox', 'current') + current_stylesheet
        self.setStyleSheet(current_stylesheet)
        self.selected = True

    def set_deselected(self):
        current_stylesheet = self.styleSheet()
        target = custom_stylesheet('groupbox', 'current')
        current_stylesheet = current_stylesheet.replace(target, '')
        self.selected = False
        self.setStyleSheet(current_stylesheet)

    def set_moved(self):
        self.moved = True
        self.deleted = False
        self.setStyleSheet(custom_stylesheet('title', 'moved'))

    def set_deleted(self):
        self.moved = False
        self.deleted = True
        self.setStyleSheet(custom_stylesheet('title', 'deleted'))

    def title_change(self, filepath: str):
        current_filepath = self.params.get('Filepath')
        if filepath != current_filepath:
            filename = os.path.basename(filepath)
            self.params['Filepath'] = filepath
            self.params['Filename'] = filename
            self.setTitle(filepath)
