# -*- coding: utf-8 -*-

from .dialog import ProgressDialog
from .dialog import PixmapLabel
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
        self.filelist_for_return = []
        self.filelist_original = []

    def init_thumbnail(self, filelist):
        self.filelist_original = filelist

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(filelist))

        base_layout = QGridLayout()
        row = col = 0

        for array in filelist:
            filepath, filename, tab_index = array

            portrait_border = QGroupBox()
            portrait_border.setMaximumWidth(190)
            portrait_border.setMinimumWidth(190)

            portrait_layout = QVBoxLayout()
            portrait_border.setLayout(portrait_layout)

            pixmap = portrait_generator(filepath)
            pixmap_label = PixmapLabel()
            pixmap_label.setMinimumSize(150, 150)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setToolTip(filename)
            pixmap_label.setObjectName(str(tab_index))
            pixmap_label.clicked.connect(self.pixmap_clicked)

            check_box = QCheckBox(filename)
            check_box.setObjectName(filename)
            check_box.stateChanged.connect(self.check_box_changed)

            portrait_layout.addWidget(pixmap_label)
            portrait_layout.addWidget(check_box)
            base_layout.addWidget(portrait_border, row, col)

            col = col + 1
            if col == 5:
                col = 0
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
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close_button_clicked)
        button_layout.addWidget(json_button)
        button_layout.addWidget(close_button)

        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(button_layout)
        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        scroll_area.setMinimumWidth(thumb.sizeHint().width() + 25)
        if row > 2:
            scroll_area.setMinimumHeight(portrait_layout.sizeHint().height() * 3)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)

        progress.close()
        self.show()
        move_centre(self, self.parent())

    def check_box_changed(self):
        filename = self.sender().objectName()
        self.sender().parent().setStyleSheet("QGroupBox {background-color: #86cecb;}")
        if self.sender().isChecked():
            for array in self.filelist_original:
                if filename == array[1]:
                    self.filelist_for_return.append(array[0])
                    break
        else:
            for array in self.filelist_original:
                self.sender().parent().setStyleSheet("")
                if filename == array[1]:
                    self.filelist_for_return.remove(array[0])

    def pixmap_clicked(self):
        target_tab = self.sender().objectName()
        self.parent().root_tab.setCurrentIndex(int(target_tab))
        self.parent().activateWindow()

    def json_button_clicked(self):
        index_list = []
        for filepath in self.filelist_for_return:
            for array in self.filelist_original:
                if filepath == array[0]:
                    index_list.append(array[2])
                    break
        self.parent().export_json_selected(index_list)

    def close_button_clicked(self):
        self.close()


class Listview(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_list = []
        self.setWindowTitle('Listview')
        self.estimated_width = 400

    def init_listview(self, dic_list):
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

        root_widget.setLayout(root_layout)
        estimated_width = root_widget.sizeHint().width() + 50
        estimated_height = group_box.sizeHint().height() * 4 + 50

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
        for tmp in ['Export JSON', 'Close']:
            button = QPushButton(tmp)
            button.setObjectName(tmp)
            footer_layout.addWidget(button)
            button.clicked.connect(self.button_push)
        return footer_layout

    def button_push(self):
        where_from = self.sender().objectName()
        if where_from == 'Close':
            self.close()

    def pixmap_labels(self, index):
        filepath = self.dictionary_list[index].get('Filepath', None)
        pixmap_label = QLabel()
        if filepath:
            pixmap = portrait_generator(filepath)
            pixmap_label.setPixmap(pixmap)
        else:
            pixmap_label.setText("Couldn't load image.")
        pixmap_label.setMinimumSize(150, 150)
        pixmap_label.setMaximumSize(150, 150)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return pixmap_label

    def groups(self, index):
        group = QGroupBox()
        group_layout = QHBoxLayout()
        status_label_layout = QGridLayout()
        pixmap_label = self.pixmap_labels(index)

        for i, key in enumerate(['Seed', 'Sampler', 'Steps', 'CFG scale', 'Model']):

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

        group_layout.addWidget(check_box)
        group_layout.addWidget(pixmap_label)
        group_layout.addLayout(status_label_layout)
        group_layout.addLayout(extension_label_layout)

        group.setLayout(group_layout)
        group.setTitle(self.dictionary_list[index].get('Filepath', 'None'))

        return group


class SearchWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.status = None
        self.extension = None
        self.search_cfg_label = None
        self.search_box = None
        self.search_model = None
        self.search_seed_box = None
        self.search_cfg = None

    def init_search_window(self, model_list):
        search_label = QLabel('Search prompt : ')
        search_seed_label = QLabel('Search seed : ')
        self.search_cfg_label = QLabel('CFG : 0')
        search_model_label = QLabel('Model : ')
        self.search_box = QLineEdit(self)
        self.search_model = QComboBox()
        self.search_seed_box = QLineEdit(self)
        self.search_cfg = QSlider()
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search)
        close_button = QPushButton('Close', self)
        close_button.clicked.connect(self.window_close)

        layout = QGridLayout()

        for i, tmp in enumerate(['Negative prompt', 'Region control']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            layout.addWidget(checkbox, 1, i + 1)

        for i, tmp in enumerate(['Exact match', 'Case sensitive']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            layout.addWidget(checkbox, 2, i + 1)

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

        status_group = QGroupBox()
        status_group.setTitle('Status')
        status_group.setCheckable(True)
        status_group.setChecked(False)
        status_group_layout = QGridLayout()

        status_group_layout.addWidget(search_model_label, 0, 0)
        status_group_layout.addWidget(self.search_model, 0, 1, 1, 3)
        model_list.insert(0, '')
        self.search_model.addItems(model_list)

        status_group_layout.addWidget(search_seed_label, 1, 0)
        status_group_layout.addWidget(self.search_seed_box, 1, 1, 1, 3)
        reg_ex = QRegularExpression('^[0-9]*')
        validator = QRegularExpressionValidator(reg_ex)
        self.search_seed_box.setValidator(validator)

        status_group_layout.addWidget(self.search_cfg_label, 2, 0)
        status_group_layout.addWidget(self.search_cfg, 2, 1, 1, 3)
        self.search_cfg.setOrientation(Qt.Orientation.Horizontal)
        self.search_cfg.setTickInterval(1)
        self.search_cfg.setRange(0, 40)
        self.search_cfg.valueChanged.connect(self.value_change)

        for i, tmp in enumerate(['Less than', 'Equal to', 'Greater than']):
            radio_button = QRadioButton(tmp)
            radio_button.setObjectName(tmp)
            status_group_layout.addWidget(radio_button, 3, i + 1)
            if tmp == 'Equal to':
                radio_button.setChecked(True)

        status_group.setLayout(status_group_layout)
        self.status = status_group

        layout.addWidget(search_label, 0, 0, 1, 1)
        layout.addWidget(self.search_box, 0, 1, 1, 3)
        layout.addWidget(status_group, 3, 0, 2, 4)
        layout.addWidget(extension_group, 5, 0, 2, 4)
        layout.addWidget(search_button, 7, 0, 1, 2)
        layout.addWidget(close_button, 7, 2, 1, 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

        self.show()
        move_centre(self, self.parent())

    def value_change(self):
        self.search_cfg_label.setText('CFG : ' + str(self.search_cfg.value() * 0.5))

    def window_close(self):
        self.close()

    def search(self):
        conditions = {}
        search_prompt = self.search_box.text()
        if search_prompt:
            conditions['Prompt'] = search_prompt

        if self.status.isChecked():
            search_model = self.search_model.currentText()
            search_seed = self.search_seed_box.text()
            search_cfg = str(self.search_cfg.value() * 0.5)
            if search_cfg != 0:
                for tmp in self.centralWidget().findChildren(QRadioButton):
                    if tmp.isChecked():
                        search_cfg = (search_cfg, tmp.objectName())
                        break
            if search_model:
                conditions['Model'] = search_model
            if search_seed:
                conditions['Seed'] = search_seed
            if search_cfg:
                conditions['CFG'] = search_cfg

        search_conditions = ['Negative prompt',
                             'Region control',
                             'Exact match',
                             'Case sensitive',
                             'LoRa / AddNet',
                             'Hires / Extras',
                             'CFG',
                             'Tiled diffusion',
                             'ControlNet',
                             'Regional prompter']

        for i, tmp in enumerate(search_conditions):
            widget = self.centralWidget().findChild(QCheckBox, tmp)
            if widget.isChecked() and i < 4:
                conditions[tmp] = True
            elif widget.isChecked() and self.extension.isChecked() and i > 3:
                conditions[tmp] = True

        self.parent().search_tab(conditions)


@lru_cache(maxsize=1000)
def portrait_generator(filepath):
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    return pixmap


def move_centre(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())
