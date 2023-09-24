# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtWidgets import QGridLayout, QTextEdit, QLineEdit, QComboBox, QSlider, QLabel, QGroupBox
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
        self._init_bar(vertical)
        self.image_current(0)

    def _init_bar(self, vertical: bool):
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

        root_layout.addLayout(self._button_area())
        root_layout.addWidget(scroll)
        self.setLayout(root_layout)

        self._tab_bar_thumbnails(self.filepaths)

    def _button_area(self):
        button_area_layout = QHBoxLayout()
        for text in [['S', 'Search'], ['R', 'Restore'], ['D', 'Diffview'], ['L', 'Listview'], ['T', 'Thumbnails']]:
            button = QPushButton(text[0])
            button.setObjectName(text[0])
            button.setToolTip(text[1])
            button.setFixedSize(25, 25)
            button.clicked.connect(self._button_clicked)
            button_area_layout.addWidget(button)
        return button_area_layout

    def _tab_bar_thumbnails(self, filepaths: list, starts=0):
        layout = self.scroll_contents.layout()
        for index, filepath in enumerate(filepaths):
            number = starts + index
            filename = os.path.basename(filepath)

            pixmap_label = PixmapLabel()
            pixmap_label.setObjectName('index_' + str(number))
            pixmap_label.setToolTip(filename)
            pixmap_label.clicked.connect(self._pixmap_clicked)
            pixmap_label.rightClicked.connect(self._pixmap_right_clicked)
            pixmap_label.ctrl_clicked.connect(self._pixmap_ctrl_clicked)
            pixmap_label.shift_clicked.connect(self._pixmap_shift_clicked)
            pixmap = portrait_generator(filepath, 100)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setFixedSize(100, 100)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setStyleSheet('border: 1px solid palette(midlight)')

            layout.addWidget(pixmap_label)

    def _pixmap_clicked(self, right=False):
        parent = self.parent().parent()
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])

        if self.selected:
            target = list(self.selected)
            for num in target:
                if num != number:
                    self._border_clear(num)

        if number != self.current:
            parent.root_tab.setCurrentIndex(number)
            if right:
                parent.pixmap_clicked()

    def _pixmap_right_clicked(self):
        self._pixmap_clicked(True)

    def _pixmap_ctrl_clicked(self):
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])

        if number in self.selected:
            if len(self.selected) > 1:
                self._border_clear(number)
            else:
                self.image_current(number)

        else:
            self.selected.add(number)
            self.sender().setStyleSheet('border: 2px solid rgba(19, 122, 127, 0.5)')

    def _pixmap_shift_clicked(self):
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
                for i in self.selected:
                    params.append(parent.params[i].params)
                diff = DiffWindow(params, parent)
                diff.show()
                diff.move_centre()
        elif where_from == 'L':
            parent.open_listview()
        elif where_from == 'T':
            parent.open_thumbnail()

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
        if self.selected:
            self.selected.discard(index)

    def add_tab(self, filepaths: list):
        add_items = [value for value in filepaths if value not in self.filepaths]
        self._tab_bar_thumbnails(add_items, len(self.filepaths))
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
        self.selected.add(index)

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


class InterrogateTab(QWidget):
    def __init__(self, result_list: list, parent=None):
        super().__init__(parent)
        self.prompt = result_list[0]
        self.rating = result_list[2]
        self.character = result_list[3]
        self.confidence = result_list[4]
        self.model = result_list[5]
        self.tag_threshold = result_list[6]
        self.chara_threshold = result_list[7]
        self.model_box = QComboBox()
        self.prompt_box = QTextEdit()
        self.tag = QLabel()
        self.chara = QLabel()
        self.setObjectName('interrogate')

        self.tag.setFixedSize(30, 25)
        self.chara.setFixedSize(30, 25)

        model_list = ('MOAT', 'SwinV2', 'ConvNext', 'ConvNextV2', 'ViT')
        model_index = next((i for i, model in enumerate(model_list) if model.lower() == self.model), next)
        self.model_box.addItems(model_list)
        self.model_box.setCurrentIndex(model_index)
        self.setContentsMargins(0, 0, 0, 0)

        self._init_ui()

    def _init_ui(self):
        root_layout = QHBoxLayout()
        main_layout = QVBoxLayout()
        confidence_layout = QVBoxLayout()

        main_layout.addLayout(self._main_section())
        main_layout.addLayout(self._footer_button())

        confidence_layout.addWidget(self._rating_section(), 1)
        confidence_layout.addWidget(self._tag_section(), 2)

        root_layout.addLayout(main_layout, 3)
        root_layout.addLayout(confidence_layout, 2)

        self.setLayout(root_layout)

    def _main_section(self):
        main_section_layout = QGridLayout()
        chara_name = 'Not applicable'
        confidence_int = 0
        confidence_percent = '-.----%'

        if self.character:
            estimated_character = sorted(self.character.items(), key=lambda x: x[1], reverse=True)
            chara_name, chara_confidence = estimated_character[0]
            chara_name = chara_name.replace('_', ' ')
            confidence_int = int(chara_confidence * 10000)
            confidence_percent = f'{chara_confidence * 100:.4f}%'

        texts = (('Model :', self.model),
                 ('Tag :', self.tag_threshold),
                 ('Character :', self.chara_threshold),
                 ('Chara. tag :', chara_name),
                 (confidence_percent, confidence_int),
                 ('Estimated tags (editable)', self.prompt))

        for index, text in enumerate(texts):
            title = QLabel(text[0])
            title.setFixedSize(75, 25)
            title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if text[0] == 'Model :':
                main_section_layout.addWidget(title, index, 0)
                main_section_layout.addWidget(self.model_box, index, 1, 1, 2)

            elif text[0] == 'Chara. tag :':
                chara_tag = QLineEdit(text[1])
                chara_tag.setReadOnly(True)
                chara_tag.setMinimumWidth(280)
                main_section_layout.addWidget(title, index, 0)
                main_section_layout.addWidget(chara_tag, index, 1, 1, 2)

            elif text[0] == 'Estimated tags (editable)':
                self.prompt_box.setText(text[1])
                self.prompt_box.setReadOnly(False)
                self.prompt_box.setMaximumHeight(125)
                title.setMinimumSize(200, 25)
                title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                main_section_layout.addWidget(title, index, 0, 1, 3)
                main_section_layout.addWidget(self.prompt_box, index + 1, 0, 1, 3)

            elif text[0] == 'Tag :' or text[0] == 'Character :':
                if text[0] == 'Tag :':
                    self.tag.setText(str(text[1]))
                    main_section_layout.addWidget(self.tag, index, 1)
                else:
                    self.chara.setText(str(text[1]))
                    main_section_layout.addWidget(self.chara, index, 1)

                slider_name = text[0].replace(' :', '')
                slider = main_slider(slider_name, int(text[1] * 100), 100)
                slider.setObjectName(slider_name)
                slider.valueChanged.connect(self._threshold_change)
                main_section_layout.addWidget(title, index, 0)
                main_section_layout.addWidget(slider, index, 2)

            else:
                slider = main_slider('chara_confidence', text[1], 10000, style_sheet(0), True)
                main_section_layout.addWidget(title, index, 0)
                main_section_layout.addWidget(slider, index, 1, 1, 2)

        return main_section_layout

    def _rating_section(self):
        rating_section = QGroupBox()
        rating_section.setTitle('Rating')
        rating_section_layout = QGridLayout()
        rating_section_layout.setSpacing(0)
        rating_confidence = sorted(self.rating.items(), key=lambda x: x[1], reverse=True)

        i = 0
        for key, item in rating_confidence:
            title = QLabel(key.capitalize())
            rating_section_layout.addWidget(title, i, 0)
            value = QLabel(f'{item * 100:.5f}%')
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rating_section_layout.addWidget(value, i, 2)
            confidence = main_slider(key, int(item * 1000000), 1000000, style_sheet(0), True)
            rating_section_layout.addWidget(confidence, i + 1, 0, 1, 3)
            i += 2

        rating_section.setLayout(rating_section_layout)
        return rating_section

    def _tag_section(self):
        tags = sorted(self.confidence.items(), key=lambda x: x[1], reverse=True)

        tag_section_group = QGroupBox()
        tag_section_group.setTitle('General tags')

        tag_section_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setStyleSheet('border: 0px;')
        scroll_area.setContentsMargins(0, 0, 0, 0)

        scroll_area_contents = QWidget()
        scroll_area_contents.setContentsMargins(0, 0, 0, 0)

        content_layout = QGridLayout()
        content_layout.setSpacing(1)
        content_layout.setColumnMinimumWidth(1, 50)

        i = 0
        for key, item in tags:
            title = QLabel(key)
            content_layout.addWidget(title, i, 0)
            value = QLabel(f'{item * 100:.5f}%')
            content_layout.addWidget(value, i, 2)
            confidence = main_slider(key, int(item * 1000000), 1000000, style_sheet(0), True)
            content_layout.addWidget(confidence, i + 1, 0, 1, 3)
            i += 2

        scroll_area_contents.setLayout(content_layout)
        scroll_area.setWidget(scroll_area_contents)
        tag_section_layout.addWidget(scroll_area)
        tag_section_group.setLayout(tag_section_layout)

        return tag_section_group

    def _footer_button(self):
        footer_button_layout = QHBoxLayout()
        for button_text in ('Export text', 'Export all text', 'Re-interrogate'):
            button = QPushButton(button_text)
            button.setObjectName(button_text)
            button.clicked.connect(self._footer_button_clicked)
            footer_button_layout.addWidget(button)
        return footer_button_layout

    def _threshold_change(self):
        where_from = self.sender().objectName()
        value = str(float(self.sender().value() / 100))

        if where_from == 'Tag':
            self.tag.setText(value)
        else:
            self.chara.setText(value)

    def _footer_button_clicked(self):
        where_from = self.sender().objectName()

        if where_from == 'Export text':
            pass
        elif where_from == 'Export all text':
            pass
        elif where_from == 'Re-interrogate':
            pass


def main_slider(name: str, value: int, slider_range: int, style=None, disabled=False):
    slider = QSlider()
    slider.setRange(0, slider_range)
    slider.setValue(value)
    slider.setObjectName(name)
    slider.setOrientation(Qt.Orientation.Horizontal)
    slider.setDisabled(disabled)

    if style:
        slider.setStyleSheet(style)

    return slider


def style_sheet(number):
    if number == 0:
        return "QSlider::handle:horizontal {height: 0px; width: 0px; border-radius: 0px; }" \
               "QSlider::sub-page {background: rgba(19, 122, 127, 0.5)}"






