# -*- coding: utf-8 -*-

import difflib
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout
from PySide6.QtWidgets import QScrollArea, QLabel, QTextEdit, QPushButton, QStackedWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from .widget import PixmapLabel
from .widget import move_centre


class ImageWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen = QApplication.primaryScreen()
        self.filepath = ''
        self.max_screen = self.screen.availableGeometry()
        self.screen_center = self.screen.geometry().center()

    def __image_window_clicked(self):
        if self.isActiveWindow():
            self.close()

    def init_image_window(self):
        label = PixmapLabel()
        pixmap = QPixmap(self.filepath)

        screen_width = int(self.max_screen.width() * 0.95)
        screen_height = int(self.max_screen.height() * 0.95)
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        width = screen_width if pixmap_width > screen_width else pixmap_width
        height = screen_height if pixmap_height > screen_height else pixmap_height

        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        title = 'Image: ' + str(pixmap.width()) + 'x' + str(pixmap.height())
        self.setWindowTitle(title)

        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.clicked.connect(self.__image_window_clicked)

        self.setCentralWidget(label)
        visible = self.isVisible()
        self.show()
        self.adjustSize()

        if not visible:
            frame_geometry = self.frameGeometry()
            frame_geometry.moveCenter(self.screen_center)
            self.move(frame_geometry.topLeft())


class DiffWindow(QMainWindow):
    def __init__(self, params: tuple, parent=None):
        super().__init__(parent)
        self.status = None
        self.params = params
        self.setWindowTitle('Diff Window')
        self.__init_diff()
        self.setMinimumSize(1000, 1000)
        move_centre(self)

    def __init_diff(self):
        statuses = ['Extensions',
                    'Timestamp',
                    'Image size',
                    'Size',
                    'Seed',
                    'Sampler',
                    'Eta',
                    'Steps',
                    'CFG scale',
                    'Model',
                    'VAE',
                    'Variation seed',
                    'Variation seed strength',
                    'Seed resize from',
                    'Denoising strength',
                    'Clip skip',
                    'ENSD',
                    'Version'
                    ]
        central_widget = QWidget()
        central_widget_layout = QHBoxLayout()
        diff = QWidget()
        diff_layout = QGridLayout()

        for i in range(len(self.params)):
            filepath = self.params[i].get('Filepath')
            filepath_label = QLabel(filepath)
            filepath_label.setFixedSize(500, 25)
            filepath_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            diff_layout.addWidget(filepath_label, 0, i)

            pixmap_label = PixmapLabel()
            pixmap = QPixmap(filepath)
            pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setFixedSize(500, 500)
            diff_layout.addWidget(pixmap_label, 1, i)

        status_widget = QStackedWidget()

        page0 = QWidget()
        page0_layout = QHBoxLayout()
        scroll_source = QScrollArea()
        scroll_target = QScrollArea()
        scroll_area_source = QWidget()
        scroll_area_target = QWidget()
        scroll_layout_source = QGridLayout()
        scroll_layout_target = QGridLayout()

        html_tag = '<span style="color: red; font-weight: bold;">@@@</span>'
        for index, status in enumerate(statuses):
            source = self.params[0].get(status, 'None')
            target = self.params[1].get(status, 'None')

            if not source == target and index > 1:
                status = html_tag.replace('@@@', status)
                source = html_tag.replace('@@@', source)
                target = html_tag.replace('@@@', target)

            key_source = QLabel()
            key_source.setTextFormat(Qt.TextFormat.RichText)
            key_source.setText(status)

            key_target = QLabel()
            key_target.setTextFormat(Qt.TextFormat.RichText)
            key_target.setText(status)

            item_source = QLabel()
            item_source.setTextFormat(Qt.TextFormat.RichText)
            item_source.setText(source)

            item_target = QLabel()
            item_target.setTextFormat(Qt.TextFormat.RichText)
            item_target.setText(target)

            scroll_layout_source.addWidget(key_source, index, 0)
            scroll_layout_source.addWidget(item_source, index, 1)
            scroll_layout_target.addWidget(key_target, index, 0)
            scroll_layout_target.addWidget(item_target, index, 1)

        scroll_area_source.setLayout(scroll_layout_source)
        scroll_area_target.setLayout(scroll_layout_target)
        scroll_source.setWidget(scroll_area_source)
        scroll_target.setWidget(scroll_area_target)

        scroll_source.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_source.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_target.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_target.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        page0_layout.addWidget(scroll_source)
        page0_layout.addWidget(scroll_target)
        page0.setLayout(page0_layout)

        page1 = QWidget()
        page1_layout = QHBoxLayout()
        source_textbox, target_textbox = self.__make_textbox('Positive')
        page1_layout.addWidget(source_textbox)
        page1_layout.addWidget(target_textbox)
        page1.setLayout(page1_layout)

        page2 = QWidget()
        page2_layout = QHBoxLayout()
        source_textbox, target_textbox = self.__make_textbox('Negative')
        page2_layout.addWidget(source_textbox)
        page2_layout.addWidget(target_textbox)
        page2.setLayout(page2_layout)

        status_widget.addWidget(page0)
        status_widget.addWidget(page1)
        status_widget.addWidget(page2)

        diff_layout.addWidget(status_widget, 2, 0, 4, 2)
        self.status = status_widget

        button_layout = QHBoxLayout()
        close_button = QPushButton('Close')
        page0_button = QPushButton('Main status')
        page1_button = QPushButton('Positive')
        page2_button = QPushButton('Negative')
        close_button.clicked.connect(lambda: self.close())
        page0_button.clicked.connect(lambda: self.status.setCurrentIndex(0))
        page1_button.clicked.connect(lambda: self.status.setCurrentIndex(1))
        page2_button.clicked.connect(lambda: self.status.setCurrentIndex(2))
        button_layout.addWidget(page0_button)
        button_layout.addWidget(page1_button)
        button_layout.addWidget(page2_button)
        button_layout.addWidget(close_button)
        diff_layout.addLayout(button_layout, 6, 0, 1, 2)

        diff.setLayout(diff_layout)
        central_widget_layout.addWidget(diff)
        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)

        self.show()

    def __make_textbox(self, key: str):
        original_source_words = self.params[0].get(key, 'None').replace('<', '&lt;').replace('>', '&gt;')
        original_target_words = self.params[1].get(key, 'None').replace('<', '&lt;').replace('>', '&gt;')
        original_source_words = original_source_words.replace('-', '<hyphen>').replace('@', '<atmark>')
        original_target_words = original_target_words.replace('-', '<hyphen>').replace('@', '<atmark>')
        source_words = original_source_words
        target_words = original_target_words
        common_words_source = []
        common_words_target = []

        while True:
            source_start, source_end, target_start, target_end = common_match(source_words, target_words)

            if source_start is None:
                break

            common_words_source.append((source_start, source_end))
            common_words_target.append((target_start, target_end))

            source_size = source_end - source_start
            target_size = target_end - target_start

            source_words = source_words[:source_start] + '-' * source_size + source_words[source_end:]
            target_words = target_words[:target_start] + '@' * target_size + target_words[target_end:]

        common_words_source = sorted(common_words_source, reverse=True)
        common_words_target = sorted(common_words_target, reverse=True)

        for starts, ends in common_words_source:
            original_source_words = insert_tag(original_source_words, starts, ends)

        for starts, ends in common_words_target:
            original_target_words = insert_tag(original_target_words, starts, ends)

        original_source_words = original_source_words.replace('\n', '<BR>').replace('<hyphen>', '-').replace('<atmark>', '@')
        original_target_words = original_target_words.replace('\n', '<BR>').replace('<hyphen>', '-').replace('<atmark>', '@')

        original_source_words = '<span style="color: red; font-weight: bold;">' + original_source_words + '</span>'
        original_target_words = '<span style="color: red; font-weight: bold;">' + original_target_words + '</span>'

        source_textbox = QTextEdit()
        source_textbox.setHtml(original_source_words)
        target_textbox = QTextEdit()
        target_textbox.setHtml(original_target_words)

        return source_textbox, target_textbox


def common_match(diff1: str, diff2: str):
    matcher = difflib.SequenceMatcher(None, diff1, diff2, autojunk=False)
    match = matcher.find_longest_match(0, len(diff1), 0, len(diff2))

    if 0 < match.size < 5:
        if diff1[match.a - 1] not in '-@' and \
           diff1[match.a + match.size] not in '-@' and \
           diff2[match.b - 1] not in '-@' and \
           diff2[match.b + match.size] not in '-@':
            return None, None, None, None

    if match.size > 5:
        start1 = match.a
        start2 = match.b
        end1 = start1 + match.size
        end2 = start2 + match.size
        return start1, end1, start2, end2

    else:
        return None, None, None, None


def insert_tag(target: str, start_pos: int, end_pos: int):
    tmp = target[:end_pos] + '</span>' + target[end_pos:]
    result = tmp[:start_pos] + '<span style="color: black; font-weight: normal;">' + tmp[start_pos:]
    return result
