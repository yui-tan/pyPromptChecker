# -*- coding: utf-8 -*-

from .widget import *
from .dialog import *
from .custom import *
from .menu import FileManageMenu
from . import config

import os
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QComboBox, QLabel
from PyQt6.QtCore import Qt, QTimer

LISTVIEW_PIXMAP = config.get('ListViewPixmapSize', 200)
MOVE_DELETE = config.get('MoveDelete', False)
HIDE_NOT_MATCH = config.get('HideNotMatchedTabs', False)
BUTTONS = (('Select all', 'Select all'),
           ('Search', 'Search'),
           ('Thumbnail', 'Thumbnail'),
           ('Tabview', 'Tabview'),
           ('Diff', 'Diff'),
           ('Add favourite', 'Add favourite'),
           ('▲M&enu', '▲Menu'))


class Listview(QMainWindow):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.toast = None
        self.root_widget = None
        self.controller = controller
        self.size = LISTVIEW_PIXMAP
        self.setWindowTitle('Listview')
        self.menu = FileManageMenu(self)

        self.footer = None
        self.borders = []

    def init_listview(self, param_list: list, moved: set = None, deleted: set = None):
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(param_list))

        self.borders = []

        estimated_height = 0

        self.root_widget = QWidget()
        root_layout = QVBoxLayout()

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        scroll_area = QScrollArea()

        for index, param in param_list:
            listview_border = ListviewBorder(index, param, self.controller, self.size, self)
            estimated_height += (listview_border.sizeHint().height() + 50)
            root_layout.addWidget(listview_border)
            self.borders.append(listview_border)

            if moved and index in moved:
                listview_border.set_moved()

            if deleted and index in deleted:
                listview_border.set_deleted()

            progress.update_value()

        self.root_widget.setLayout(root_layout)

        estimated_width = self.root_widget.sizeHint().width() + 50
        estimated_height = 800 if estimated_height > 800 else estimated_height

        scroll_area.setWidget(self.root_widget)
        scroll_area.setMinimumWidth(estimated_width)
        scroll_area.setMinimumHeight(estimated_height)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.footer = FooterButtons(BUTTONS, self, self.controller)

        central_widget_layout.addLayout(self.__header_section())
        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addWidget(self.footer)

        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        self.show()
        self.resize(estimated_width, estimated_height)
        move_centre(self)

    def signal_received(self):
        where_from = self.sender().objectName()
        selected_index = set()

        for border in self.borders:
            if border.selected:
                selected_index.add(border.index)

        if where_from == 'Add favourite':
            result = self.controller.request_reception(selected_index, 'add')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Delete':
            result = self.controller.request_reception(selected_index, 'delete')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Move':
            result = self.controller.request_reception(selected_index, 'move')
            if result:
                self.toast.init_toast('Moved!', 1000)
        elif where_from == 'Export JSON':
            result = self.controller.request_reception(selected_index, 'json')
            if result:
                self.toast.init_toast('Exported!', 1000)
        elif where_from == 'Interrogate':
            self.controller.request_reception(selected_index, 'interrogate')
        elif where_from == 'Diff':
            self.controller.request_reception(selected_index, 'diff')
        elif where_from == 'Search':
            self.controller.request_reception(selected_index, 'search')
        elif where_from == 'Select all':
            self.__select_all_toggle(len(selected_index))
        elif where_from == 'Restore':
            self.search_process(None)
        elif where_from == 'Close':
            self.close()

    def listview_add_images(self, param_list: list):
        progress = None
        if self.isActiveWindow():
            progress = ProgressDialog()
            progress.setLabelText('Loading...')
            progress.setRange(0, len(param_list))

        layout = self.root_widget.layout()

        for index, param in param_list:
            listview_border = ListviewBorder(index, param, self.controller, self.size, self)
            layout.addWidget(listview_border)
            self.borders.append(listview_border)

            if progress:
                progress.update_value()

    def search_process(self, indexes: tuple = None):
        if indexes:
            for border in self.borders:
                if border.index in indexes:
                    border.show()
                    border.set_matched()
                else:
                    border.clear_matched()
                    if HIDE_NOT_MATCH:
                        border.hide()
        else:
            for border in self.borders:
                border.show()
                border.clear_matched()

    def manage_subordinates(self, index: int, detail: str, remarks=None):
        for border in self.borders:
            if border.index == index:
                if detail == 'moved':
                    border.set_moved()
                    if remarks:
                        border.title_change(remarks)
                if detail == 'deleted':
                    border.set_deleted()
                    if remarks:
                        border.title_change(remarks)
                if border.selected:
                    border.set_deselected()
                break

    def get_selected_images(self, selected=True):
        result = []
        for border in self.borders:
            if border.selected and selected:
                result.append(border.index)
            elif not selected:
                result.append(border.index)
        return result

    def __header_section(self):
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
            combo_box.currentIndexChanged.connect(self.__status_changed)
            header_layout.addWidget(combo_box, row, col)
            combo_box.addItems(combo_items)
            combo_box.setCurrentText(status)
            col += 1
            if col == 4:
                row += 1
                col = 0

        return header_layout

    def __status_changed(self):
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

            for border in self.borders:
                value = border.params.get(search_str, 'None')
                title_label = border.findChild(QLabel, status_number + '_title')
                value_label = border.findChild(QLabel, status_number + '_value')

                title_label.setText(status_str)
                value_label.setText(value)

    def __select_all_toggle(self, count):
        if count == len(self.borders):
            for border in self.borders:
                border.set_deselected()
        else:
            for border in self.borders:
                border.set_selected()


class ListviewBorder(ClickableGroup):
    def __init__(self, index: int, params: dict, controller, size: int = 200, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.size = size
        self.index = index
        self.params = params
        self.pixmap_label = None
        self.status_labels = []
        self.selected = False
        self.moved = False
        self.deleted = False
        self.matched = False
        self.changed = 0
        self.status = ['Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version']
        self.__init_class()

        self.setObjectName(f'group_{index}')
        self.clicked.connect(self.__toggle_selected)

    def __init_class(self):
        layout = QHBoxLayout()

        layout.addWidget(self.__pixmap_label())
        layout.addLayout(self.__status_labels())
        layout.addLayout(self.__extension_labels())

        self.setLayout(layout)
        self.setTitle(self.params.get('Filepath', 'None'))

    def __pixmap_label(self):
        filepath = self.params.get('Filepath')
        pixmap = portrait_generator(filepath, self.size)
        pixmap_label = PixmapLabel()
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setFixedSize(self.size, self.size)
        pixmap_label.clicked.connect(self.__toggle_selected)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap_label.setObjectName(f'pixmap_{self.index}')
        return pixmap_label

    def __status_labels(self):
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

    def __extension_labels(self):
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

    def __toggle_selected(self):
        if self.parent_window.isActiveWindow():
            if 'group' in self.sender().objectName() and self.changed == 0:
                if self.selected:
                    self.set_deselected()
                else:
                    self.set_selected()
                self.changed = 1

            elif 'pixmap' in self.sender().objectName() and self.changed == 0:
                self.controller.request_reception((self.index,), 'view')
                self.changed = 1

            self.timer = QTimer()
            self.timer.timeout.connect(self.__initialize_changed)
            self.timer.start(10)

    def __initialize_changed(self):
        self.changed = 0
        self.timer.stop()

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

    def set_matched(self):
        self.matched = True
        self.setStyleSheet(custom_stylesheet('title', 'matched'))

    def clear_matched(self):
        if self.moved:
            self.set_moved()
        elif self.deleted:
            self.set_deleted()
        else:
            self.setStyleSheet('')

    def title_change(self, filepath: str):
        current_filepath = self.params.get('Filepath')
        if filepath != current_filepath:
            filename = os.path.basename(filepath)
            self.params['Filepath'] = filepath
            self.params['Filename'] = filename
            self.setTitle(filepath)
