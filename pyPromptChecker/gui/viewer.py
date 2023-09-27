# -*- coding: utf-8 -*-

import difflib
from .widget import PixmapLabel
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt6.QtWidgets import QScrollArea, QLabel, QTextEdit, QSplitter, QPushButton
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ImageWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen = QApplication.primaryScreen()
        self.filepath = ''
        self.max_screen = self.screen.availableGeometry()
        self.screen_center = self.screen.geometry().center()

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
        label.clicked.connect(self.clicked)

        self.setCentralWidget(label)
        visible = self.isVisible()
        self.show()
        self.adjustSize()

        if not visible:
            self.move_centre()

    def clicked(self):
        self.close()

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())


class DiffWindow(QMainWindow):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params
        self.setWindowTitle('Diff Window')
        self.init_diff()
        self.setMinimumSize(1000, 1000)

    def init_diff(self):
        statuses = ['Filepath',
                    'Extensions',
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
            pixmap_label = PixmapLabel()
            pixmap = QPixmap(self.params[i].get('Filepath'))
            pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setFixedSize(500, 500)

            diff_layout.addWidget(pixmap_label, 0, i)

        scroll_source = QScrollArea()
        scroll_target = QScrollArea()
        scroll_area_source = QWidget()
        scroll_area_target = QWidget()
        scroll_layout_source = QGridLayout()
        scroll_layout_target = QGridLayout()

        html_tag = '<span style="color: red; font-weight: bold;">@@@</span>'
        source_splitter = QSplitter(Qt.Orientation.Vertical)
        target_splitter = QSplitter(Qt.Orientation.Vertical)
        for index, status in enumerate(statuses):
            source = self.params[0].get(status, 'None')
            target = self.params[1].get(status, 'None')

            if status == 'Variation seed':
                status = 'Var. seed'
            elif status == 'Variation seed strength':
                status = 'Var. strength'
            elif status == 'Seed resize from':
                status = 'Resize from'
            elif status == 'Denoising strength':
                status = 'Denoising'

            if not source == target and index > 2:
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

        source_splitter.addWidget(scroll_source)
        target_splitter.addWidget(scroll_target)

        for key in ['Positive', 'Negative']:
            source_textbox, target_textbox = self.make_textbox(html_tag, key)
            source_splitter.addWidget(source_textbox)
            target_splitter.addWidget(target_textbox)

        diff_layout.addWidget(source_splitter, 1, 0, 4, 1)
        diff_layout.addWidget(target_splitter, 1, 1, 4, 1)

        close_button = QPushButton('Close')
        close_button.clicked.connect(lambda: self.close())
        diff_layout.addWidget(close_button, 5, 0, 1, 2)

        diff.setLayout(diff_layout)
        central_widget_layout.addWidget(diff)
        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)

    def make_textbox(self, html_tag, key):
        source_words = self.params[0].get(key, 'None')
        target_words = self.params[1].get(key, 'None')
        source_words_list = source_words.split()
        target_words_list = target_words.split()

        difference = difflib.Differ()
        differ = list(difference.compare(source_words_list, target_words_list))
        changed_words = [word for word in differ if word.startswith('- ') or word.startswith('+ ')]
        source_searched_position = 0
        target_searched_position = 0
        html_source = ''
        html_target = ''

        for word in changed_words:
            differ_word = html_tag.replace('@@@', word[2:])
            if word[0] == '-':
                position = source_words.find(word[2:], source_searched_position)
                html_source += source_words[source_searched_position:position].replace('\n', '<BR>') + differ_word
                source_searched_position = position + len(word[2:])
            else:
                position = target_words.find(word[2:], target_searched_position)
                html_target += target_words[target_searched_position:position].replace('\n', '<BR>') + differ_word
                target_searched_position = position + len(word[2:])

        if source_searched_position < len(source_words):
            html_source += source_words[source_searched_position:].replace('\n', '<BR>')

        if target_searched_position < len(target_words):
            html_target += target_words[target_searched_position:].replace('\n', '<BR>')

        source_textbox = QTextEdit()
        source_textbox.setHtml(html_source)
        target_textbox = QTextEdit()
        target_textbox.setHtml(html_target)

        return source_textbox, target_textbox

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
