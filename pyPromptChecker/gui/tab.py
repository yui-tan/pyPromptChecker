# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QGridLayout
from PyQt6.QtCore import Qt, QTimer
from .viewer import DiffWindow
from .dialog import PixmapLabel
from .widget import portrait_generator


class TabBar(QWidget):
    def __init__(self, filepaths: list, vertical=False, parent=None):
        super().__init__(parent)
        self.scroll_contents = QWidget()
        self.diff_button = QPushButton()
        self.scroll_contents.setContentsMargins(0, 0, 0, 0)
        self.filepaths = filepaths
        self.current = 0
        self.moved = set()
        self.deleted = set()
        self.matched = set()
        self.selected = set()
        self.init_bar(vertical)
        self.image_current(0)

    def init_bar(self, vertical: bool):
        root_layout = QVBoxLayout() if vertical else QHBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setContentsMargins(0, 0, 0, 0)
        scroll.setStyleSheet('border: none; padding: 0px')

        if not vertical:
            scroll.setFixedHeight(140)
            scroll.setMinimumWidth(10)

        else:
            scroll.setFixedWidth(140)
            scroll.setMinimumHeight(10)

        layout = QVBoxLayout() if vertical else QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        self.scroll_contents.setLayout(layout)
        scroll.setWidget(self.scroll_contents)

        root_layout.addLayout(self.button_area())
        root_layout.addWidget(scroll)
        self.setLayout(root_layout)

        self.tab_bar_thumbnails(self.filepaths)

    def button_area(self):
        button_area_layout = QHBoxLayout()
        for text in [['S', 'Search'], ['R', 'Restore'], ['D', 'Diffview'], ['L', 'Listview'], ['T', 'Thumbnails']]:
            button = QPushButton(text[0])
            button.setObjectName(text[0])
            button.setToolTip(text[1])
            button.setFixedSize(25, 25)
            button.clicked.connect(self._button_clicked)
            button_area_layout.addWidget(button)
        return button_area_layout

    def add_tab(self, filepaths: list):
        add_items = [value for value in filepaths if value not in self.filepaths]
        self.tab_bar_thumbnails(add_items, len(self.filepaths))
        self.filepaths.extend(add_items)

    def toggle_tab_bar(self, where_from):
        if self.isHidden():
            self.show()
            where_from.setText('<')
        else:
            parent = self.parent().parent()
            self.hide()
            timer = QTimer(self)
            timer.timeout.connect(lambda: parent.adjustSize())
            timer.start(10)
            where_from.setText('>')

    def tab_bar_thumbnails(self, filepaths: list, starts=0):
        layout = self.scroll_contents.layout()
        for index, filepath in enumerate(filepaths):
            number = starts + index
            filename = os.path.basename(filepath)

            pixmap_label = PixmapLabel()
            pixmap_label.setObjectName('index_' + str(number))
            pixmap_label.setToolTip(filename)
            pixmap_label.clicked.connect(self.pixmap_clicked)
            pixmap_label.rightClicked.connect(self.pixmap_right_clicked)
            pixmap_label.ctrl_clicked.connect(self.pixmap_ctrl_clicked)
            pixmap_label.shift_clicked.connect(self.pixmap_shift_clicked)
            pixmap = portrait_generator(filepath, 100)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setFixedSize(100, 100)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setStyleSheet('border: 1px solid palette(midlight)')

            layout.addWidget(pixmap_label)

    def pixmap_clicked(self, right=False):
        parent = self.parent().parent()
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])

        if self.selected:
            target = list(self.selected)
            for num in target:
                if num != number:
                    self._border_clear(num)
                self.selected.remove(num)

        if number != self.current:
            parent.root_tab.setCurrentIndex(number)
            if right:
                parent.pixmap_clicked()

    def pixmap_right_clicked(self):
        self.pixmap_clicked(True)

    def pixmap_ctrl_clicked(self):
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])

        if not self.selected:
            self.selected.add(self.current)

        if number in self.selected:
            self._border_clear(number)
            self.selected.discard(number)

        else:
            self.selected.add(number)
            self.sender().setStyleSheet('border: 2px solid rgba(19, 122, 127, 0.5)')

    def pixmap_shift_clicked(self):
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])
        if self.current != number:
            starts = min(self.current, number)
            ends = max(self.current, number)
            for i in range(starts, ends + 1):
                label = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(i))
                label.setStyleSheet('border: 2px solid rgba(19, 122, 127, 0.5)')
                if i not in self.selected:
                    self.selected.add(i)

    def _button_clicked(self):
        where_from = self.sender().objectName()
        parent = self.parent().parent()
        if where_from == 'S':
            parent.tab_search_window()
        elif where_from == 'R':
            self.result_clear()
        elif where_from == 'D':
            if len(self.selected) == 2:
                params = []
                parent = self.parent().parent()
                for i in self.selected:
                    params.append(parent.params[i].params)
                diff = DiffWindow(params, parent)
                diff.show()
                diff.move_centre()
        elif where_from == 'L':
            parent.open_listview()
        elif where_from == 'T':
            parent.open_thumbnail()

    def pixmap_hide(self):
        for index in range(len(self.scroll_contents.findChildren(PixmapLabel))):
            if index not in self.matched:
                target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(index))
                target.hide()

    def image_moved(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(0, 0, 255, 0.5)'
        self._border_change(indexes, stylesheet)
        self.moved.update(indexes)

    def image_deleted(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(255, 0, 0, 0.5)'
        self._border_change(indexes, stylesheet)
        self.deleted.update(indexes)

    def image_matched(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(0, 255, 0, 0.5)'
        self._border_change(indexes, stylesheet)
        self.matched.update(indexes)

    def image_current(self, index: int):
        stylesheet = 'border: 2px solid rgba(19, 122, 127, 0.5)'
        self._border_clear(self.current)
        self._border_change([index], stylesheet)
        self.current = index

    def image_default(self, index: int):
        stylesheet = 'border: 1px solid palette(midlight)'
        self._border_change([index], stylesheet)

    def result_clear(self):
        self.matched.clear()
        widgets = self.scroll_contents.findChildren(PixmapLabel)
        for widget in widgets:
            if widget.isHidden:
                widget.show()
            tmp = widget.objectName()
            index = int(tmp.split('_')[1])
            self._border_clear(index)
        self.image_current(self.current)

    def _border_change(self, indexes: list, stylesheet: str):
        for index in indexes:
            target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(index))
            target.setStyleSheet(stylesheet)

    def _border_clear(self, index: int):
        if self.moved and index in self.moved:
            self.image_moved([index])
        elif self.deleted and index in self.deleted:
            self.image_deleted([index])
        elif self.matched and index in self.matched:
            self.image_matched([index])
        else:
            self.image_default(index)


class InnerTab(QTabWidget):
    pass
