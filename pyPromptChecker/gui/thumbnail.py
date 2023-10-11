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
           ('Thumbnail', 'Thumbnail'),
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
        self.size = THUMBNAIL_PIXMAP
        self.estimated_height = self.size + 67
        self.estimated_width = self.size + 40
        self.setWindowTitle('Thumbnail View')
        custom_keybindings(self)

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

    def key_binds_send(self, request: str):
        if request == 'append':
            result = self.controller.request_reception(request, sender=self, conditions='files')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif request == 'replace':
            result = self.controller.request_reception(request, sender=self, conditions='files')
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif request == 'exit':
            self.controller.request_reception(request, sender=self)
        elif request == 'theme':
            self.controller.request_reception(request, sender=self)

    def signal_received(self, right: bool = False):
        where_from = self.sender().objectName()
        selected_index = set()

        for border in self.borders:
            if border.selected:
                selected_index.add(border.index)
        selected_index = tuple(selected_index)

        if where_from == 'Add favourite':
            result = self.controller.request_reception('add', self, selected_index)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Delete':
            result = self.controller.request_reception('delete', self, selected_index)
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Move':
            result = self.controller.request_reception('move', self, selected_index)
            if result:
                self.toast.init_toast('Moved!', 1000)
        elif where_from == 'Export JSON':
            result = self.controller.request_reception('json', self, selected_index)
            if result:
                self.toast.init_toast('Exported!', 1000)
        elif where_from == 'Import Json file replace':
            result = self.controller.request_reception('import', self, ('files', False))
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'Import Json dir replace':
            result = self.controller.request_reception('import', self, ('files', False))
            if result:
                self.toast.init_toast('Imported!', 1000)
        elif where_from == 'Append file':
            result = self.controller.request_reception('append', self, conditions='files')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Append dir':
            result = self.controller.request_reception('append', self, conditions='directory')
            if result:
                self.toast.init_toast('Added!', 1000)
        elif where_from == 'Replace file':
            result = self.controller.request_reception('replace', self, conditions='files')
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'Replace dir':
            result = self.controller.request_reception('replace', self, conditions='directory')
            if result:
                self.toast.init_toast('Replaced!', 1000)
        elif where_from == 'Interrogate':
            result = self.controller.request_reception('interrogate', self, selected_index)
            if result:
                self.toast.init_toast('Interrogated!', 1000)
        elif where_from == 'Diff':
            self.controller.request_reception('diff', self, selected_index)
        elif where_from == 'Search':
            self.controller.request_reception('search', self)
        elif where_from == 'Listview':
            self.controller.request_reception('list', self)
        elif where_from == 'Tabview':
            self.controller.request_reception('tab', self)
        elif where_from == 'Select all':
            self.__select_all_toggle(selected_index)
        elif where_from == 'Restore':
            self.search_process(None)
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
        self.label = None
        self.pixmap_label = None
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
