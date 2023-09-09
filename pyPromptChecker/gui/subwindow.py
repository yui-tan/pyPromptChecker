# -*- coding: utf-8 -*-

from .dialog import ProgressDialog
from .dialog import PixmapLabel
from .dialog import MessageBox
from functools import lru_cache
from PyQt6.QtWidgets import QMainWindow, QApplication, QGridLayout, QGroupBox, QCheckBox, QScrollArea, QSlider
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QSpacerItem, QLineEdit, QComboBox
from PyQt6.QtWidgets import QRadioButton
from PyQt6.QtGui import QPixmap, QImageReader, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression


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

        pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)

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
            move_centre(self)

    def clicked(self):
        self.close()


class ThumbnailView(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Thumbnail View')

    def init_thumbnail(self, dictionary_list, size):

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(dictionary_list))

        base_layout = QGridLayout()
        row = col = width = 0

        for index, dictionary in enumerate(dictionary_list):
            filepath = dictionary.get('Filepath')
            filename = dictionary.get('Filename')

            portrait_border = QGroupBox()
            portrait_border.setMaximumWidth(size + 40)
            portrait_border.setMinimumWidth(size + 40)

            portrait_layout = QVBoxLayout()
            portrait_border.setLayout(portrait_layout)

            pixmap = portrait_generator(filepath, size)
            pixmap_label = PixmapLabel()
            pixmap_label.setMinimumSize(size, size)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setToolTip(filename)
            pixmap_label.setObjectName(str(index))
            pixmap_label.clicked.connect(self.pixmap_clicked)

            check_box = QCheckBox(filename)
            check_box.setObjectName(str(index))
            check_box.toggled.connect(self.check_box_changed)

            portrait_layout.addWidget(pixmap_label)
            portrait_layout.addWidget(check_box)
            base_layout.addWidget(portrait_border, row, col)

            width += (size + 40)
            col += 1

            if width > 900:
                col = width = 0
                row = row + 1

            progress.update_value()

        thumb = QWidget()
        thumb.setLayout(base_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(thumb)

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        json_button = QPushButton('Export selected images JSON')
        json_button.clicked.connect(self.json_button_clicked)
        button_layout.addWidget(json_button)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close_button_clicked)
        button_layout.addWidget(close_button)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(button_layout)
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        scroll_area.setMinimumWidth(thumb.sizeHint().width() + 25)

        estimated_height = portrait_layout.sizeHint().height()
        if row > 2:
            if estimated_height < 300:
                scroll_area.setMinimumHeight(estimated_height * 3)
            else:
                scroll_area.setMaximumHeight(estimated_height + 25)

        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()

        self.show()
        move_centre(self, self.parent())

    def check_box_changed(self):
        if self.sender().isChecked():
            self.sender().parent().setStyleSheet("QGroupBox {border: 1px solid #86cecb; }")
        else:
            self.sender().parent().setStyleSheet("")

    def pixmap_clicked(self):
        target_tab = self.sender().objectName()
        self.parent().root_tab.setCurrentIndex(int(target_tab))
        self.parent().activateWindow()

    def json_button_clicked(self):
        indexes = []
        for widget in self.centralWidget().findChildren(QCheckBox):
            if widget.isChecked():
                index = widget.objectName()
                indexes.append(int(index))
        if indexes:
            self.parent().export_json_selected(indexes)

    def close_button_clicked(self):
        self.close()


class Listview(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_list = []
        self.setWindowTitle('Listview')
        self.estimated_width = 400
        self.size = 0

    def init_listview(self, dic_list, size):
        self.size = size
        self.dictionary_list = dic_list
        file_counts = len(self.dictionary_list)

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        root_widget = QWidget()
        root_layout = QVBoxLayout()

        for i in range(file_counts):
            group_box = self.groups(i)
            root_layout.addWidget(group_box)

        groupbox_count = 4 if file_counts > 4 else file_counts
        root_widget.setLayout(root_layout)
        estimated_width = root_widget.sizeHint().width() + 50
        estimated_height = group_box.sizeHint().height() * groupbox_count + 50
        if estimated_height > 750:
            estimated_height = 750

        scroll_area.setWidget(root_widget)
        scroll_area.setMinimumWidth(estimated_width)
        scroll_area.setMinimumHeight(estimated_height)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self.footer_button())

        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)
        self.show()
        move_centre(self, self.parent())

    def footer_button(self):
        footer_layout = QHBoxLayout()
        for tmp in ['Export selected JSON', 'Close']:
            button = QPushButton(tmp)
            button.setObjectName(tmp)
            footer_layout.addWidget(button)
            button.clicked.connect(self.button_push)
        return footer_layout

    def button_push(self):
        where_from = self.sender().objectName()
        if where_from == 'Close':
            self.close()
        elif where_from == 'Export selected JSON':
            self.check_group()

    def pixmap_label(self, index):
        filepath = self.dictionary_list[index].get('Filepath', None)
        pixmap_label = PixmapLabel()
        if filepath:
            pixmap = portrait_generator(filepath, self.size)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.clicked.connect(self.pixmap_clicked)
            pixmap_label.setObjectName(str(index))
        else:
            pixmap_label.setText("Couldn't load image.")
        pixmap_label.setMinimumSize(self.size, self.size)
        pixmap_label.setMaximumSize(self.size, self.size)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return pixmap_label

    def groups(self, index):
        group = QGroupBox()
        group.setObjectName(str(index))
        group_layout = QHBoxLayout()
        status_label_layout = QGridLayout()
        pixmap_label = self.pixmap_label(index)

        for i, key in enumerate(['Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version']):

            item = self.dictionary_list[index].get(key, 'None')
            title_label = QLabel(key)
            status_label = QLabel(item)
            spacer_1 = QSpacerItem(20, 20)
            spacer_2 = QSpacerItem(20, 20)

            size_policy_title = title_label.sizePolicy()
            size_policy_value = status_label.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(5)
            title_label.setSizePolicy(size_policy_title)
            status_label.setSizePolicy(size_policy_value)

            title_label.setMinimumHeight(20)
            status_label.setMinimumHeight(20)
            title_label.setMaximumHeight(20)
            status_label.setMaximumHeight(20)
            status_label.setMinimumWidth(200)

            status_label_layout.addItem(spacer_1, i, 0)
            status_label_layout.addWidget(title_label, i, 1)
            status_label_layout.addItem(spacer_2, i, 2)
            status_label_layout.addWidget(status_label, i, 3)

        j = 0
        k = 0
        addnet = any(key in v for v in self.dictionary_list[index] for key in ['Lora', 'Ti in prompt', 'Add network'])
        cfg = any(key in v for v in self.dictionary_list[index] for key in ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler'])

        extension_label_layout = QGridLayout()

        for condition_list in [
            [self.dictionary_list[index].get('Extensions', '---'), 'Extension'],
            ['Extras', 'Extras' in self.dictionary_list[index]],
            ['Variation', 'Variation seed' in self.dictionary_list[index]],
            ['Hires.fix', 'Hires upscaler' in self.dictionary_list[index]],
            ['Lora/AddNet', addnet],
            ['CFG', cfg],
            ['Tiled Diffusion', 'Tiled diffusion' in self.dictionary_list[index]],
            ['ControlNet', 'ControlNet' in self.dictionary_list[index]],
            ['Regional', 'RP Active' in self.dictionary_list[index]]
        ]:

            title, status = condition_list

            extension_label = QLabel(title)
            extension_label.setMaximumWidth(100)
            extension_label.setMinimumWidth(100)
            extension_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if not status:
                extension_label.setDisabled(True)
                extension_label.setStyleSheet("border-radius: 5px ; border: 1px solid palette(shadow);")
            elif status == 'Extension':
                style_sheet = "border-radius: 5px ;" \
                              "border: 2px solid @@@ ;" \
                              "background-color: @@@ ;" \
                              "color: white ;"
                if title == 'PNG':
                    style_sheet = style_sheet.replace('@@@', 'green')
                    extension_label.setStyleSheet(style_sheet)
                elif title == 'JPEG':
                    style_sheet = style_sheet.replace('@@@', 'blue')
                    extension_label.setStyleSheet(style_sheet)
                elif title == 'WEBP':
                    style_sheet = style_sheet.replace('@@@', 'red')
                    extension_label.setStyleSheet(style_sheet)
                else:
                    extension_label.setDisabled(True)
                    extension_label.setStyleSheet("border-radius: 5px ; border: 1px solid palette(shadow);")
            else:
                extension_label.setStyleSheet("border-radius: 5px ;"
                                              "border: 2px solid palette(highlight) ;"
                                              "background-color: palette(highlight) ;"
                                              "color: white ;")
            extension_label_layout.addWidget(extension_label, j, k)
            if j == 4:
                k += 1
                j = 0
            else:
                j += 1

        check_box = QCheckBox('')
        check_box.setStyleSheet("QCheckBox { spacing: 0px; }")
        check_box.toggled.connect(self.group_toggle)

        group_layout.addWidget(check_box)
        group_layout.addWidget(pixmap_label)
        group_layout.addLayout(status_label_layout)
        group_layout.addLayout(extension_label_layout)

        group.setLayout(group_layout)
        group.setTitle(self.dictionary_list[index].get('Filepath', 'None'))

        return group

    def pixmap_clicked(self):
        target_tab = self.sender().objectName()
        self.parent().root_tab.setCurrentIndex(int(target_tab))
        self.parent().activateWindow()

    def group_toggle(self):
        if self.sender().isChecked():
            self.sender().parent().setStyleSheet("QGroupBox {border: 1px solid #86cecb; }")
        else:
            self.sender().parent().setStyleSheet("")

    def check_group(self):
        indexes = []
        for widget in self.centralWidget().findChildren(QCheckBox):
            if widget.isChecked():
                index = widget.parent().objectName()
                indexes.append(int(index))
        if indexes:
            self.parent().export_json_selected(indexes)


class SearchWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.conditions = {}
        self.result = 'Tabs'
        self.prompt = None
        self.status = None
        self.extension = None
        self.search_box = None
        self.search_model = None
        self.search_seed_box = None
        self.search_cfg_label = None

    def init_search_window(self, model_list):
        layout = QGridLayout()

        result_label = QLabel('Result shows: ')
        result_box = QComboBox()
        result_box.addItems(['Tabs', 'Listview', 'Thumbnails'])
        result_box.currentIndexChanged.connect(self.result_change)

        prompt_group = QGroupBox()
        prompt_group.setTitle('Search Keywords')
        prompt_group.setCheckable(True)
        prompt_group.setChecked(True)
        prompt_group_layout = QGridLayout()

        search_label = QLabel('Search words : ')
        self.search_box = QLineEdit(self)

        for i, tmp in enumerate(['Positive', 'Negative', 'Region control']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            prompt_group_layout.addWidget(checkbox, 2, i + 1)
            if tmp == 'Positive':
                checkbox.setChecked(True)

        checkbox = QCheckBox('Case insensitive')
        checkbox.setObjectName('Case insensitive')
        prompt_group_layout.addWidget(checkbox, 3, 2, 1, 2)

        checkbox = QCheckBox('Use regex')
        checkbox.setObjectName('Use regex')
        checkbox.setDisabled(True)
        prompt_group_layout.addWidget(checkbox, 3, 1)

        prompt_group_layout.addWidget(search_label, 1, 0)
        prompt_group_layout.addWidget(self.search_box, 1, 1, 1, 3)
        prompt_group.setLayout(prompt_group_layout)
        self.prompt = prompt_group

        status_group = QGroupBox()
        status_group.setTitle('Status')
        status_group.setCheckable(True)
        status_group.setChecked(False)
        status_group_layout = QGridLayout()

        search_model_label = QLabel('Model : ')
        self.search_model = QComboBox()
        self.search_model.addItems(model_list)

        status_group_layout.addWidget(search_model_label, 0, 0)
        status_group_layout.addWidget(self.search_model, 0, 1, 1, 3)

        search_seed_label = QLabel('Search seed : ')
        self.search_seed_box = QLineEdit(self)
        reg_ex = QRegularExpression('^[0-9]*')
        validator = QRegularExpressionValidator(reg_ex)
        self.search_seed_box.setValidator(validator)

        self.search_cfg_label = QLabel('CFG : 0')
        search_cfg = QSlider()
        search_cfg.setOrientation(Qt.Orientation.Horizontal)
        search_cfg.setTickInterval(1)
        search_cfg.setRange(0, 40)
        search_cfg.valueChanged.connect(self.value_change)

        for i, tmp in enumerate(['Less than', 'Equal to', 'Greater than']):
            radio_button = QRadioButton(tmp)
            radio_button.setObjectName(tmp)
            status_group_layout.addWidget(radio_button, 3, i + 1)
            if tmp == 'Equal to':
                radio_button.setChecked(True)

        status_group_layout.addWidget(search_seed_label, 1, 0)
        status_group_layout.addWidget(self.search_seed_box, 1, 1, 1, 3)
        status_group_layout.addWidget(self.search_cfg_label, 2, 0)
        status_group_layout.addWidget(search_cfg, 2, 1, 1, 3)

        status_group.setLayout(status_group_layout)
        self.status = status_group

        extension_group = QGroupBox()
        extension_group.setTitle('Extensions')
        extension_group.setCheckable(True)
        extension_group.setChecked(False)
        extension_group_layout = QGridLayout()

        for i, tmp in enumerate(['LoRa / AddNet', 'Hires / Extras', 'CFG']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            extension_group_layout.addWidget(checkbox, 0, i)

        for i, tmp in enumerate(['Tiled diffusion', 'ControlNet', 'Regional prompter']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            extension_group_layout.addWidget(checkbox, 1, i)

        extension_group.setLayout(extension_group_layout)
        self.extension = extension_group

        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search)
        close_button = QPushButton('Close', self)
        close_button.clicked.connect(self.window_close)

        layout.addWidget(result_label, 0, 0)
        layout.addWidget(result_box, 0, 1, 1, 3)
        layout.addWidget(prompt_group, 1, 0, 2, 4)
        layout.addWidget(status_group, 4, 0, 2, 4)
        layout.addWidget(extension_group, 6, 0, 2, 4)
        layout.addWidget(search_button, 8, 0, 1, 2)
        layout.addWidget(close_button, 8, 2, 1, 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.show()
        move_centre(self, self.parent())

    def result_change(self):
        self.result = self.sender().currentText()

    def value_change(self):
        self.search_cfg_label.setText('CFG : ' + str(self.sender().value() * 0.5))

    def window_close(self):
        self.close()

    def search(self):
        self.conditions['Result'] = self.result
        if self.prompt.isChecked():
            self.conditions['Search'] = self.search_box.text()
            for tmp in self.prompt.findChildren(QCheckBox):
                key = tmp.objectName()
                self.conditions[key] = tmp.isChecked()
        self.conditions['Prompt'] = self.prompt.isChecked()

        if self.status.isChecked():
            relation = 'Greater than'
            for tmp in self.status.findChildren(QRadioButton):
                if tmp.isChecked():
                    relation = tmp.objectName()
                    break

            keys = ['Model', 'Seed', 'CFG', 'Relation']
            seek = [self.search_model.currentText(),
                    self.search_seed_box.text(),
                    self.search_cfg_label.text().replace('CFG : ', ''),
                    relation]

            for index, key in enumerate(keys):
                self.conditions[key] = seek[index]
        self.conditions['Status'] = self.status.isChecked()

        if self.extension.isChecked():
            for tmp in self.extension.findChildren(QCheckBox):
                self.conditions[tmp.objectName()] = tmp.isChecked()
        self.conditions['Extension'] = self.extension.isChecked()

        if self.validation():
            self.parent().tab_search(self.conditions)

    def validation(self):
        words = self.conditions.get('Search', 'None')
        count = words.count('"')

        if count % 2 != 0:
            text = 'There are not an even number of double quotes.'
            MessageBox(text, 'Please check it out', 'ok', 'info', self)
            return False

        if ' | ' in words:
            text = 'There is space on either side of |.'
            MessageBox(text, 'Please check it out', 'ok', 'info', self)
            return False

        return True


@lru_cache(maxsize=1000)
def portrait_generator(filepath, size):
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    return pixmap


def move_centre(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())
