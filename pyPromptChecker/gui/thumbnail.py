# -*- coding: utf-8 -*-

from .dialog import *
from .widget import *
from .menu import FooterButtonMenu
from .custom import *
from . import config

import os
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.toast = None
        self.controller = controller
        self.size = config.get('ThumbnailPixmapSize', 150)
        self.estimated_height = self.size + 67
        self.estimated_width = self.size + 40
        self.setWindowTitle('Thumbnail View')
        self.menu = FooterButtonMenu(self)

        self.borders = []
        self.pos_x = 0
        self.pos_y = 0
        self.max_x = 0
        self.max_y = 0

    def init_thumbnail(self, param_list: list, moved: set = None, deleted: set = None):
        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(param_list))

        thumbnails = QWidget()
        thumbnails.setObjectName('thumbnail_view')
        thumbnails_layout = QGridLayout()

        self.borders = []
        self.pos_x = 0
        self.pos_y = 0
        self.max_x = 0
        self.max_y = 0

        for index, param in param_list:
            self.max_y = self.pos_y + 1
            self.max_x = max(self.pos_x + 1, self.max_x)
            portrait_border = ThumbnailBorder(index, param, self.size, self.controller, self)
            self.borders.append(portrait_border)
            thumbnails_layout.addWidget(portrait_border, self.pos_y, self.pos_x)

            if moved and index in moved:
                portrait_border.set_moved()

            if deleted and index in deleted:
                portrait_border.set_deleted()

            if self.pos_x * self.estimated_width < 900:
                self.pos_x += 1
            else:
                self.pos_x = 0
                self.pos_y += 1

            progress.update_value()

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
        central_widget_layout.addLayout(self.__footer_buttons())
        central_widget.setLayout(central_widget_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        estimated_height = min(self.estimated_height * self.max_y + 70, 1000)
        estimated_width = self.estimated_width * self.max_x + 210

        self.show()
        self.resize(estimated_width, estimated_height)
        move_centre(self)

        self.toast = Toast(self)

        progress.close()

        scroll_area.setMinimumWidth(0)

    def signal_received(self):
        where_from = self.sender().objectName()
        selected_index = set()

        for border in self.borders:
            if border.selected:
                selected_index.add(border.index)

        if where_from == '▲Menu':
            x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
            y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.controller.main_menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.controller.main_menu.exec(adjusted_pos)
        elif where_from == 'Add favourite':
            result = self.controller.request_reception(selected_index, 'add')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Delete':
            result = self.controller.request_reception(selected_index, 'delete')
            if result:
                self.toast.init_toast('Deleted!', 1000)
        elif where_from == 'Move':
            result = self.controller.request_reception(selected_index, 'move')
            if result:
                self.toast.init_toast('Moved!', 1000)
        elif where_from == 'Export JSON':
            result = self.controller.request_reception(selected_index, 'json')
            if result:
                self.toast.init_toast('Exported!', 1000)
        elif where_from == 'Import Json file replace':
            result = self.controller.request_reception(('files', False), 'import')
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'Import Json dir replace':
            result = self.controller.request_reception(('dir', False), 'import')
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'Append file':
            result = self.controller.request_reception(('files',), 'append', sender=self)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Append dir':
            result = self.controller.request_reception(('directory',), 'append', sender=self)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Replace file':
            result = self.controller.request_reception(('files',), 'replace', sender=self)
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'Replace dir':
            result = self.controller.request_reception(('directory',), 'replace', sender=self)
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'Interrogate':
            self.controller.request_reception(selected_index, 'interrogate')
        elif where_from == 'Diff':
            self.controller.request_reception(selected_index, 'diff')
        elif where_from == 'Search':
            self.controller.request_reception(selected_index, 'search')
        elif where_from == 'List':
            self.controller.request_reception(selected_index, 'list')
        elif where_from == 'Tab':
            self.controller.request_reception(selected_index, 'tab')
        elif where_from == 'Select all':
            self.__select_all_toggle(len(selected_index))
        elif where_from == 'Close':
            self.close()

    def thumbnail_add_images(self, param_list: list):
        progress = None
        if self.isActiveWindow():
            progress = ProgressDialog()
            progress.setLabelText('Loading...')
            progress.setRange(0, len(param_list))

        layout = self.centralWidget().findChild(QWidget, 'thumbnail_view').layout()

        for index, param in param_list:
            self.max_y = self.pos_y + 1
            self.max_x = max(self.pos_x + 1, self.max_x)
            portrait_border = ThumbnailBorder(index, param, self.size, self.controller, self)
            self.borders.append(portrait_border)
            layout.addWidget(portrait_border, self.pos_y, self.pos_x)

            if self.pos_x * self.estimated_width < 900:
                self.pos_x += 1
            else:
                self.pos_x = 0
                self.pos_y += 1

            if progress:
                progress.update_value()

    def manage_subordinates(self, index: int, detail: str, remarks=None):
        for border in self.borders:
            if border.index == index:
                if detail == 'moved':
                    border.set_moved()
                    if remarks:
                        border.label_change(remarks)
                if detail == 'deleted':
                    border.set_deleted()
                    if remarks:
                        border.label_change(remarks)
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

    def __footer_buttons(self):
        button_layout = QHBoxLayout()
        management = config.get('MoveDelete', False)
        buttons = ('Select all', 'Search', 'Diff', 'Interrogate', 'Export JSON', '▲Menu')

        if management:
            buttons = ('Select all', 'List', 'Tab', 'Diff', 'Interrogate', 'Export JSON', 'Add favourite', '▲Menu')

        for button_text in buttons:
            button = ButtonWithMenu()
            button.setText(button_text)
            button.setObjectName(button_text)
            button_layout.addWidget(button)
            button.clicked.connect(self.signal_received)

            if button_text == 'Add favourite':
                button.rightClicked.connect(self.__footer_submenu)

        return button_layout

    def __footer_submenu(self):
        x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
        y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.menu.sizeHint().height()
        adjusted_pos = QPoint(x, y)
        self.menu.exec(adjusted_pos)

    def __select_all_toggle(self, count):
        if count == len(self.borders):
            for border in self.borders:
                border.set_deselected()
        else:
            for border in self.borders:
                border.set_selected()


class ThumbnailBorder(ClickableGroup):
    def __init__(self, index: int, params: dict, size: int = 150, controller=None, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.controller = controller
        self.size = size
        self.index = index
        self.params = params
        self.label = None
        self.pixmap_label = None
        self.selected = False
        self.moved = False
        self.deleted = False
        self.__init_class()

        self.setObjectName(f'group_{self.index}')
        self.clicked.connect(self.__toggle_selected)

    def __init_class(self):
        layout = QVBoxLayout()
        self.setFixedSize(self.size + 60, self.size + 60)

        self.__pixmap_label()
        self.__filename_label()

        filename = self.params.get('Filename')
        self.pixmap_label.setToolTip(self.__tooltip())
        self.label.setText(filename)

        layout.addWidget(self.pixmap_label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)

    def __pixmap_label(self):
        filepath = self.params.get('Filepath')
        pixmap = portrait_generator(filepath, self.size)
        pixmap_label = PixmapLabel()
        pixmap_label.setFixedSize(self.size, self.size)
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        pixmap_label.setObjectName(f'pixmap_{self.index}')
        pixmap_label.rightClicked.connect(self.__pixmap_clicked)
        self.pixmap_label = pixmap_label

    def __tooltip(self):
        result = ''
        for key in ('Filename', 'Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version'):
            status = self.params.get(key, 'None')
            result += f'{key} : {status}\n'
        result = result.rstrip('\n')
        return result

    def __filename_label(self):
        label = HoverLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedHeight(30)
        self.label = label

    def __pixmap_clicked(self):
        if self.parent_window.isActiveWindow():
            self.controller.request_reception((self.index,), 'view')

    def __toggle_selected(self):
        if self.parent_window.isActiveWindow():
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
            self.pixmap_label.setToolTip(self.__tooltip())
