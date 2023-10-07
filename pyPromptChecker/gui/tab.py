# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QSplitter
from PyQt6.QtWidgets import QGridLayout, QTextEdit, QLineEdit, QComboBox, QSlider, QLabel, QGroupBox
from PyQt6.QtCore import Qt, QTimer

from .viewer import DiffWindow
from .widget import PixmapLabel
from .widget import portrait_generator
from .widget import move_centre
from .custom import *
from .dialog import Toast
from . import config


class TabBar(QWidget):
    def __init__(self, filepaths: list, vertical=False, parent=None):
        super().__init__(parent)
        self.scroll_contents = QWidget()
        self.diff_button = QPushButton()
        self.filepaths = filepaths

        self.current = 0
        self.moved = set()
        self.deleted = set()
        self.matched = set()
        self.selected = set()

        self.__init_bar(vertical)

        self.image_current(0)

    def __init_bar(self, vertical: bool):
        root_layout = QVBoxLayout() if vertical else QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)

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

        layout = QVBoxLayout() if vertical else QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_contents.setLayout(layout)
        scroll.setWidget(self.scroll_contents)

        root_layout.addLayout(self.__button_area())
        root_layout.addWidget(scroll)
        self.setLayout(root_layout)

        self._tab_bar_thumbnails(self.filepaths)

    def __button_area(self):
        button_area_layout = QHBoxLayout()
        button_area_layout.setContentsMargins(0, 0, 0, 0)
        for text in (('S', 'Search'), ('R', 'Restore'), ('D', 'Diffview'), ('L', 'Listview'), ('T', 'Thumbnails')):
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
                move_centre(diff)
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


class InterrogateTab(QStackedWidget):
    def __init__(self, result_list: list, parent=None, link=None):
        super().__init__(parent)
        self.root_tab = link
        self.sync = False
        self.page0 = QWidget()
        self.page1 = None
        self.page2 = None

        self.filepath = result_list[0]
        self.model = result_list[1]
        self.tag_threshold = result_list[2]
        self.chara_threshold = result_list[3]
        self.prompt = result_list[4]
        self.rating = result_list[6]
        self.character = result_list[7]
        self.confidence = result_list[8]
        self.prompt_box_1 = QTextEdit()
        self.prompt_box_2 = QTextEdit()
        self.setObjectName('interrogate')

        self._init_page0()
        self._init_page1()
        self._init_page2()

        self.setCurrentIndex(1)

    def _init_page1(self):
        page1_layout = QGridLayout()
        page1_layout.setSpacing(5)

        main_group = QGroupBox()
        main_group_layout = QGridLayout()

        current_model = '----'
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
                model_box = QComboBox()
                model_box.currentIndexChanged.connect(self._model_change)
                main_group_layout.addWidget(title, index, 0)
                main_group_layout.addWidget(model_box, index, 1, 1, 2)

                model_list = ('MOAT', 'Swin', 'ConvNext', 'ConvNextV2', 'ViT')
                model_index = next((i for i, model in enumerate(model_list) if model.lower() == self.model), next)
                current_model = model_list[model_index]
                model_box.addItems(model_list)
                model_box.setCurrentIndex(model_index)

            elif text[0] == 'Chara. tag :':
                chara_tag = QLineEdit(text[1])
                chara_tag.setReadOnly(True)
                main_group_layout.addWidget(title, index, 0)
                main_group_layout.addWidget(chara_tag, index, 1, 1, 2)

            elif text[0] == 'Estimated tags (editable)':
                self.prompt_box_1.setText(self.prompt)
                self.prompt_box_1.setObjectName('prompt_1')
                self.prompt_box_1.textChanged.connect(self._text_box_1_changed)
                page1_layout.addWidget(self.prompt_box_1, 1, 0, 1, 2)

            elif text[0] == 'Tag :' or text[0] == 'Character :':
                if text[0] == 'Tag :':
                    tag_label = QLabel()
                    tag_label.setText(str(text[1]))
                    tag_label.setObjectName('tag_label')
                    tag_label.setFixedSize(50, 25)
                    main_group_layout.addWidget(tag_label, index, 1)
                else:
                    chara_label = QLabel()
                    chara_label.setText(str(text[1]))
                    chara_label.setObjectName('chara_label')
                    chara_label.setFixedSize(50, 25)
                    main_group_layout.addWidget(chara_label, index, 1)

                slider_name = text[0].replace(' :', '')
                slider = main_slider(slider_name, int(text[1] * 100), 100)
                slider.setObjectName(slider_name)
                slider.valueChanged.connect(self._threshold_change)
                main_group_layout.addWidget(title, index, 0)
                main_group_layout.addWidget(slider, index, 2)

            else:
                style = custom_stylesheet('slider', 'confidence')
                slider = main_slider('chara_confidence', text[1], 10000, style, True)
                main_group_layout.addWidget(title, index, 0)
                main_group_layout.addWidget(slider, index, 1, 1, 2)

        main_group.setTitle(current_model + ' / ' + 'Tag : ' + str(self.tag_threshold) + ' / ' + 'Character : ' + str(self.chara_threshold))
        main_group.setLayout(main_group_layout)
        main_group.setMinimumWidth(300)
        page1_layout.addWidget(main_group, 0, 0)

        rating_group = self._rating_section()
        rating_group.setMinimumWidth(300)
        page1_layout.addWidget(rating_group, 0, 1)

        page1_layout.addLayout(self._footer_button(), 3, 0, 1, 2)

        if self.page1:
            delete_page = self.page1
            delete_page.setParent(None)
            delete_page.deleteLater()
            self.page1 = None
        self.page1 = QWidget()
        self.page1.setLayout(page1_layout)
        self.addWidget(self.page1)

    def _init_page2(self):
        page2_layout = QVBoxLayout()
        page2_layout.setSpacing(5)
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)

        tag_confidence_group = self._tag_section()
        buttons = self._footer_button(2)
        self.prompt_box_2.setText(self.prompt)
        self.prompt_box_2.setObjectName('prompt_2')
        self.prompt_box_2.textChanged.connect(self._text_box_2_changed)

        splitter.addWidget(tag_confidence_group)
        splitter.addWidget(self.prompt_box_2)
        splitter.setContentsMargins(0, 0, 0, 0)

        page2_layout.addWidget(splitter)
        page2_layout.addLayout(buttons)

        if self.page2:
            delete_page = self.page2
            delete_page.setParent(None)
            delete_page.deleteLater()
            self.page2 = None
        self.page2 = QWidget()
        self.page2.setLayout(page2_layout)
        self.addWidget(self.page2)

    def _init_page0(self):
        page3_layout = QHBoxLayout()
        label = QLabel('Now loading...')

        page3_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.page0.setLayout(page3_layout)
        self.addWidget(self.page0)

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
            value = QLabel(f'{item * 100:.4f}%')
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rating_section_layout.addWidget(value, i, 2)
            style = custom_stylesheet('slider', 'confidence')
            confidence = main_slider(key, int(item * 1000000), 1000000, style, True)
            rating_section_layout.addWidget(confidence, i + 1, 0, 1, 3)
            i += 2

        rating_section.setLayout(rating_section_layout)
        return rating_section

    def _tag_section(self):
        minimum_size = config.get('PixmapSize', 350)
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
        content_layout.setSpacing(0)

        i = 0
        for key, item in tags:
            title = QLabel(key)
            content_layout.addWidget(title, i, 0)
            value = QLabel(f'{item * 100:.4f}%')
            content_layout.addWidget(value, i, 2, alignment=Qt.AlignmentFlag.AlignRight)
            style = custom_stylesheet('slider', 'confidence')
            confidence = main_slider(key, int(item * 1000000), 1000000, style, True)
            confidence.setMinimumWidth(minimum_size + 275)
            content_layout.addWidget(confidence, i + 1, 0, 1, 3)
            i += 2

        scroll_area_contents.setLayout(content_layout)
        scroll_area.setWidget(scroll_area_contents)
        tag_section_layout.addWidget(scroll_area)
        tag_section_group.setLayout(tag_section_layout)

        return tag_section_group

    def _footer_button(self, where_from=1):
        footer_button_layout = QHBoxLayout()
        for button_text in ('Export text', 'Export all text', 'Re-interrogate', 'Tag confidence'):
            if where_from == 2 and button_text == 'Tag confidence':
                button_text = 'Main status'
            button = QPushButton(button_text)
            button.setObjectName(button_text)
            button.clicked.connect(self._footer_button_clicked)
            footer_button_layout.addWidget(button)
        return footer_button_layout

    def _text_box_1_changed(self):
        if not self.sync:
            self.sync = True
            text = self.prompt_box_1.toPlainText()
            self.prompt_box_2.setPlainText(text)
            self.sync = False

    def _text_box_2_changed(self):
        if not self.sync:
            self.sync = True
            text = self.prompt_box_2.toPlainText()
            self.prompt_box_1.setPlainText(text)
            self.sync = False

    def _model_change(self):
        self.model = self.sender().currentText().lower()

    def _threshold_change(self):
        where_from = self.sender().objectName()
        value = float(self.sender().value() / 100)
        value_str = str(value)

        if where_from == 'Tag':
            target = self.sender().parent().findChild(QLabel, 'tag_label')
            target.setText(value_str)
            self.tag_threshold = value
        else:
            target = self.sender().parent().findChild(QLabel, 'chara_label')
            target.setText(value_str)
            self.chara_threshold = value

    def _footer_button_clicked(self):
        where_from = self.sender().objectName()

        if where_from == 'Export text':
            self.export_text()
        elif where_from == 'Export all text':
            self.root_tab.export_all_text()
        elif where_from == 'Re-interrogate':
            self.re_interrogate()
        elif where_from == 'Tag confidence':
            self.setCurrentIndex(2)
        elif where_from == 'Main status':
            self.setCurrentIndex(1)

    def export_text(self, external=False):
        destination_dir = os.path.dirname(self.filepath)
        destination_filename = os.path.splitext(os.path.basename(self.filepath))[0] + '.txt'
        destination = os.path.join(destination_dir, destination_filename)
        export_str = self.prompt_box_1.toPlainText()
        with open(destination, 'w', encoding='utf-8') as f:
            f.write(export_str)
        if os.path.exists(destination):
            if not external:
                toast = Toast(self.root_tab)
                toast.init_toast('Exported', 1000)

    def re_interrogate(self):
        from pyPromptChecker.lora import interrogate
        self.setCurrentIndex(0)

        result_list = interrogate(self.model, self.filepath, self.tag_threshold, self.chara_threshold)

        self.model = result_list[1]
        self.prompt = result_list[4]
        self.rating = result_list[6]
        self.character = result_list[7]
        self.confidence = result_list[8]

        self._init_page1()
        self._init_page2()

        self.setCurrentIndex(1)


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
