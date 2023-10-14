# -*- coding: utf-8 -*-

from .dialog import *
from .widget import *
from .custom import *
from . import config

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QVBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget

THUMBNAIL_PIXMAP = config.get('ThumbnailPixmapSize', 150)
MOVE_DELETE = config.get('MoveDelete', False)
HIDE_NOT_MATCH = config.get('HideNotMatchedTabs', False)
BUTTONS = (('Select all', 'Select all'),
           ('Listview', 'Listview'),
           ('Tabview', 'Tabview'),
           ('Diff', 'Diff'),
           ('Interrogate', 'Interrogate'),
           ('Search', 'Search'),
           ('Add favourite', 'Add favourite'),
           ('▲M&enu', '▲Menu'))


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.toast = None
        self.controller = controller
        self.estimated_height = THUMBNAIL_PIXMAP + 67
        self.estimated_width = THUMBNAIL_PIXMAP + 40
        self.setWindowTitle('Thumbnail View')
        custom_keybindings(self)

        self.header = None
        self.footer = None
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
            portrait_border = ThumbnailBorder(index, param, THUMBNAIL_PIXMAP, self.controller, self)
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

        self.header = QLabel('0 image selected')
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        central_widget_layout.addWidget(self.header)

        scroll_area.setMinimumWidth(thumbnails.sizeHint().width() + 25)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)
        central_widget_layout.addWidget(scroll_area)

        self.footer = FooterButtons(BUTTONS, self, self.controller)
        central_widget_layout.addWidget(self.footer)
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

    def signal_received(self, right: bool = False):
        where_from = self.sender().objectName().lower()
        selected_index = set()

        for border in self.borders:
            if border.selected:
                selected_index.add(border.index)
        selected_index = tuple(selected_index)

        if where_from == 'add favourite':
            result = self.controller.request_reception('add', self, selected_index)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'delete':
            result = self.controller.request_reception('delete', self, selected_index)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'move':
            result = self.controller.request_reception('move', self, selected_index)
            if result:
                self.toast.init_toast('Moved!', 1000)
        elif where_from == 'interrogate':
            result = self.controller.request_reception('interrogate', self, selected_index)
            if result:
                self.toast.init_toast('Interrogated!', 1000)
        elif where_from == 'export jSON':
            result = self.controller.request_reception('json', self, selected_index)
            if result:
                self.toast.init_toast('Exported!', 1000)
        elif where_from == 'import json file replace':
            result = self.controller.request_reception('import', self, ('files', False))
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'import json dir replace':
            result = self.controller.request_reception('import', self, ('files', False))
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'append file':
            result = self.controller.request_reception('append', self, conditions='files')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'append dir':
            result = self.controller.request_reception('append', self, conditions='directory')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'replace_file':
            result = self.controller.request_reception('replace', self, conditions='files')
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'replace dir':
            result = self.controller.request_reception('replace', self, conditions='directory')
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'diff':
            self.controller.request_reception('diff', self, selected_index)
        elif where_from == 'search':
            self.controller.request_reception('search', self)
        elif where_from == 'listview':
            self.controller.request_reception('list', self)
        elif where_from == 'tabview':
            self.controller.request_reception('tab', self)
        elif where_from == 'theme':
            self.controller.request_reception('theme', self)
        elif where_from == 'exit':
            self.controller.request_reception('exit', self)
        elif where_from == 'select all':
            self.__select_all_toggle(selected_index)
        elif where_from == 'restore':
            self.search_process()
        elif where_from == 'close':
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
            portrait_border = ThumbnailBorder(index, param, THUMBNAIL_PIXMAP, self.controller, self)
            self.borders.append(portrait_border)
            layout.addWidget(portrait_border, self.pos_y, self.pos_x)

            if self.pos_x * self.estimated_width < 900:
                self.pos_x += 1
            else:
                self.pos_x = 0
                self.pos_y += 1

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

    def update_selected(self):
        indexes = self.get_selected_images(True)
        text = f'{str(len(indexes))} image selected'
        self.header.setText(text)

    def __select_all_toggle(self, count: tuple):
        if len(count) == len(self.borders):
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
        self.pixmap_label = PixmapLabel(self)
        self.label = QLabel(self)
        self.selected = False
        self.moved = False
        self.deleted = False
        self.matched = False
        self.__init_class()

        self.setObjectName(f'group_{self.index}')
        self.clicked.connect(self.__toggle_selected)

    def __init_class(self):
        layout = QVBoxLayout()
        self.setFixedSize(self.size + 60, self.size + 60)

        self.__pixmap_label()
        self.__filename_label()

        layout.addWidget(self.pixmap_label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)

    def __pixmap_label(self):
        filepath = self.params.get('Filepath')
        pixmap = portrait_generator(filepath, self.size)
        self.pixmap_label.setFixedSize(self.size, self.size)
        self.pixmap_label.setPixmap(pixmap)
        self.pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.pixmap_label.setObjectName(f'pixmap_{self.index}')
        self.pixmap_label.rightClicked.connect(self.__pixmap_clicked)
        self.pixmap_label.setToolTip(self.__tooltip())

    def __tooltip(self):
        result = ''
        for key in ('Filename', 'Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version'):
            status = self.params.get(key, 'None')
            result += f'{key} : {status}\n'
        result = result.rstrip('\n')
        return result

    def __filename_label(self):
        filename = self.params.get('Filename')
        self.label.setStyleSheet(custom_stylesheet('label', 'leave'))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.label.setFixedHeight(30)
        self.label.setText(filename)

    def __pixmap_clicked(self):
        if self.parent_window.isActiveWindow():
            self.controller.request_reception('view', self.parent_window, indexes=(self.index,))

    def __toggle_selected(self):
        if self.parent_window.isActiveWindow():
            if self.selected:
                self.set_deselected()
            else:
                self.set_selected()

    def set_selected(self):
        self.selected = True
        self.setStyleSheet(custom_stylesheet('groupbox', 'current'))
        self.parent_window.update_selected()

    def set_deselected(self):
        self.selected = False
        self.setStyleSheet('')
        self.parent_window.update_selected()

    def set_moved(self):
        self.label.setStyleSheet(custom_stylesheet('colour', 'moved'))
        self.moved = True
        self.deleted = False

    def set_deleted(self):
        self.label.setStyleSheet(custom_stylesheet('colour', 'deleted'))
        self.moved = False
        self.deleted = True

    def set_matched(self):
        self.label.setStyleSheet(custom_stylesheet('colour', 'matched'))
        self.matched = True

    def clear_matched(self):
        if self.moved:
            self.set_moved()
        elif self.deleted:
            self.set_deleted()
        else:
            self.label.setStyleSheet(custom_stylesheet('label', 'leave'))

    def label_change(self, filepath: str):
        current_filepath = self.params.get('Filepath')
        if filepath != current_filepath:
            filename = os.path.basename(filepath)
            self.params['Filepath'] = filepath
            self.params['Filename'] = filename
            self.label.setText(filename)
            self.pixmap_label.setToolTip(self.__tooltip())

    def enterEvent(self, event):
        current_style = self.label.styleSheet()

        if current_style is not None:
            stylesheet = custom_stylesheet('label', 'hover')
            current_style += ';' + stylesheet
            self.label.setStyleSheet(current_style)

    def leaveEvent(self, event):
        current_style = self.label.styleSheet()

        if current_style is not None:
            stylesheet = custom_stylesheet('label', 'leave')
            target_part = custom_stylesheet('label', 'hover')
            current_style = current_style.replace(target_part, stylesheet)
            self.label.setStyleSheet(current_style)
