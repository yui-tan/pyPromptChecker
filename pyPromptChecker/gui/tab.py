# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QTabWidget
from PyQt6.QtCore import Qt, QTimer
from .dialog import PixmapLabel
from .widget import portrait_generator


class TabBar(QWidget):
    def __init__(self, filepaths: list, vertical=False, parent=None):
        super().__init__(parent)
        self.scroll_contents = None
        self.filepaths = filepaths
        self.current = -1
        self.moved = []
        self.deleted = []
        self.matched = []
        self.init_bar(vertical)
        self.current_change(0)

    def init_bar(self, vertical: bool):
        root_layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet('border: none; padding: 0px')

        if not vertical:
            scroll.setFixedHeight(140)
            scroll.setMinimumWidth(10)
        else:
            scroll.setFixedWidth(140)
            scroll.setMinimumHeight(10)

        self.scroll_contents = QWidget()
        self.scroll_contents.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout() if vertical else QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        self.scroll_contents.setLayout(layout)
        scroll.setWidget(self.scroll_contents)

        root_layout.addWidget(scroll)
        self.setLayout(root_layout)

        self.tab_bar_thumbnails(self.filepaths)

    def add_tab(self, filepaths: list):
        add_items = [value for value in filepaths if value not in self.filepaths]
        self.tab_bar_thumbnails(add_items, len(self.filepaths))
        self.filepaths.extend(add_items)
        pass

    def toggle_tab(self):
        if self.isHidden():
            self.show()
        else:
            parent = self.parent().parent()
            self.hide()
            timer = QTimer(self)
            timer.timeout.connect(lambda: parent.adjustSize())
            timer.start(10)

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
        if number != self.current:
            parent.root_tab.setCurrentIndex(number)
            if right:
                parent.pixmap_clicked()

    def pixmap_right_clicked(self):
        self.pixmap_clicked(True)

    def image_moved(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(0, 0, 255, 0.5)'
        self.border_change(indexes, stylesheet)
        self.moved.extend(indexes)

    def image_deleted(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(255, 0, 0, 0.5)'
        self.border_change(indexes, stylesheet)
        self.deleted.extend(indexes)

    def image_matched(self, indexes: list):
        stylesheet = 'border: 2px solid rgba(0, 255, 0, 0.5)'
        self.border_change(indexes, stylesheet)
        self.matched.extend(indexes)

    def image_default(self):
        stylesheet = 'border: 1px solid palette(midlight)'
        self.border_change(self.matched, stylesheet)
        self.matched = []

    def border_change(self, indexes: list, stylesheet):
        for index in indexes:
            target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(index))
            target.setStyleSheet(stylesheet)

    def current_change(self, index: int):
        stylesheet = 'border: 1px solid palette(midlight)'

        if self.deleted:
            if self.current in self.deleted:
                stylesheet = 'border: 2px solid rgba(255, 0, 0, 0.5)'

        if self.moved:
            if self.current in self.moved:
                stylesheet = 'border: 2px solid rgba(0, 0, 255, 0.5)'

        if self.matched:
            if self.current in self.matched:
                stylesheet = 'border: 2px solid rgba(0, 255, 0, 0.5)'

        target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(index))
        target.setStyleSheet('border: 2px solid rgba(19, 122, 127, 0.5)')

        if self.current > -1:
            target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(self.current))
            target.setStyleSheet(stylesheet)

        self.current = index


class InnerTab(QTabWidget):
    pass
