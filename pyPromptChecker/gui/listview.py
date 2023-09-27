# -*- coding: utf-8 -*-

from . import config
from .dialog import ProgressDialog
from .viewer import DiffWindow
from .widget import PixmapLabel
from .widget import ClickableGroup
from .widget import portrait_generator
from .widget import make_keybindings
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea
from PyQt6.QtWidgets import QWidget, QComboBox, QLabel, QPushButton, QSpacerItem
from PyQt6.QtCore import Qt, QTimer


class Listview(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size = config.get('ListViewPixmapSize', 200)
        self.setWindowTitle('Listview')
        self.param_list = []
        self.status = ['Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version']
        self.selected = set()
        self.changed = 0
        make_keybindings(self)

    def init_listview(self, param_list):
        self.setCentralWidget(None)
        self.param_list = param_list
        file_counts = len(param_list)

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, file_counts)

        root_widget = QWidget()
        root_layout = QVBoxLayout()

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        group_box = None

        for file_count in range(file_counts):
            group_box = self._groups(file_count)
            root_layout.addWidget(group_box)
            progress.update_value()

        root_widget.setLayout(root_layout)

        groupbox_count = 4 if file_counts > 4 else file_counts
        estimated_width = root_widget.sizeHint().width() + 50
        estimated_height = group_box.sizeHint().height() * groupbox_count + 50
        estimated_height = 750 if estimated_height > 750 else estimated_height

        scroll_area.setWidget(root_widget)
        scroll_area.setMinimumWidth(estimated_width)
        scroll_area.setMinimumHeight(estimated_height)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        central_widget_layout.addLayout(self._header_section())
        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self._footer_section())

        central_widget.setLayout(central_widget_layout)

        self.setCentralWidget(central_widget)

        self.show()
        self.move_centre()

    def _groups(self, index):
        group = ClickableGroup()
        group.setObjectName(f'group_{index}')
        group.clicked.connect(self._listview_clicked)
        group_layout = QHBoxLayout()

        status_label_layout = QGridLayout()
        pixmap_label = self._pixmap_label(index)

        for i, key in enumerate(self.status):
            item = self.param_list[index].get(key, 'None')

            title_label = QLabel(key)
            title_label.setObjectName(f'{i}_title')
            status_label = QLabel(item)
            status_label.setObjectName(f'{i}_value')
            spacer_1 = QSpacerItem(20, 20)
            spacer_2 = QSpacerItem(20, 20)

            size_policy_title = title_label.sizePolicy()
            size_policy_value = status_label.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(5)
            title_label.setSizePolicy(size_policy_title)
            status_label.setSizePolicy(size_policy_value)

            title_label.setFixedSize(100, 20)
            status_label.setFixedHeight(20)
            status_label.setMinimumWidth(200)

            status_label_layout.addItem(spacer_1, i, 0)
            status_label_layout.addWidget(title_label, i, 1)
            status_label_layout.addItem(spacer_2, i, 2)
            status_label_layout.addWidget(status_label, i, 3)

        j = 0
        k = 0
        creation = 'T2I'
        addnet = any(key in v for v in self.param_list[index] for key in ['Lora', 'Textual inversion', 'Add network'])
        cfg = any(key in v for v in self.param_list[index] for key in
                  ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler'])

        if any(key in v for v in self.param_list[index] for key in ['Upscaler', 'Extras']):
            creation = 'I2I'
        if self.param_list[index].get('Positive') == 'This file has no embedded data':
            creation = '---'
        if 'Mask blur' in self.param_list[index]:
            creation = 'inpaint'

        extension_label_layout = QGridLayout()

        for condition_list in [
            [self.param_list[index].get('Extensions', '---'), 'Extension'],
            [creation, 'Creation'],
            ['Extras', 'Extras' in self.param_list[index]],
            ['Variation', 'Variation seed' in self.param_list[index]],
            ['Hires.fix', 'Hires upscaler' in self.param_list[index]],
            ['Lora/AddNet', addnet],
            ['CFG', cfg],
            ['Tiled Diffusion', 'Tiled diffusion' in self.param_list[index]],
            ['ControlNet', 'ControlNet' in self.param_list[index]],
            ['Regional', 'RP Active' in self.param_list[index]]
        ]:

            title, status = condition_list

            extension_label = QLabel(title)
            extension_label.setMaximumWidth(100)
            extension_label.setMinimumWidth(100)
            extension_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if not status:
                extension_label.setDisabled(True)
                extension_label.setStyleSheet(style_sheet('extension_label_disabled'))

            elif status == 'Extension':
                style = style_sheet('extension_label')
                if title == 'PNG':
                    style = style.replace('@@@', 'green')
                    extension_label.setStyleSheet(style)
                elif title == 'JPEG':
                    style = style.replace('@@@', 'blue')
                    extension_label.setStyleSheet(style)
                elif title == 'WEBP':
                    style = style.replace('@@@', 'red')
                    extension_label.setStyleSheet(style)
                else:
                    extension_label.setDisabled(True)
                    extension_label.setStyleSheet(style_sheet('extension_label_disabled'))

            elif status == 'Creation':
                style = style_sheet('extension_label')
                if title == 'I2I' or title == 'inpaint':
                    style = style.replace('@@@', 'red')
                    extension_label.setStyleSheet(style)
                    if title == 'inpaint':
                        extension_label.setText('inpaint')
                    else:
                        extension_label.setText('img2img')

                elif title == 'T2I':
                    style = style.replace('@@@', 'palette(highlight)')
                    extension_label.setStyleSheet(style)
                    extension_label.setText('txt2img')

                else:
                    extension_label.setDisabled(True)
                    extension_label.setStyleSheet(style_sheet('extension_label_disabled'))
            else:
                extension_label.setStyleSheet(style_sheet('extension_label_available'))

            extension_label_layout.addWidget(extension_label, j, k)

            if j == 4:
                k += 1
                j = 0
            else:
                j += 1

        group_layout.addWidget(pixmap_label)
        group_layout.addLayout(status_label_layout)
        group_layout.addLayout(extension_label_layout)

        group.setLayout(group_layout)
        group.setTitle(self.param_list[index].get('Filepath', 'None'))

        return group

    def _pixmap_label(self, index):
        filepath = self.param_list[index].get('Filepath', None)
        pixmap_label = PixmapLabel()
        if filepath:
            pixmap = portrait_generator(filepath, self.size)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.clicked.connect(self._listview_clicked)
            pixmap_label.setObjectName(f'pixmap_{index}')
        else:
            pixmap_label.setText("Couldn't load image.")
        pixmap_label.setMinimumSize(self.size, self.size)
        pixmap_label.setMaximumSize(self.size, self.size)
        pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return pixmap_label

    def _header_section(self):
        row = 1
        col = 0
        header_layout = QGridLayout()
        header_label = QLabel('Status')
        combo_items = ['Timestamp',
                       'Size',
                       'Seed',
                       'Sampler',
                       'Eta',
                       'Steps',
                       'CFG scale',
                       'Model',
                       'VAE',
                       'Var. seed',
                       'Var. strength',
                       'Resize from',
                       'Denoising',
                       'Clip skip',
                       'ENSD',
                       'Version'
                       ]

        header_label.setMinimumWidth(50)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header_label, 0, 0, 1, 4)

        for index, status in enumerate(self.status):
            combo_box = QComboBox()
            combo_box.setObjectName(f'status_{index}')
            combo_box.currentIndexChanged.connect(self._status_changed)
            header_layout.addWidget(combo_box, row, col)
            combo_box.addItems(combo_items)
            combo_box.setCurrentText(status)
            col += 1
            if col == 4:
                row += 1
                col = 0

        return header_layout

    def _footer_section(self):
        footer_layout = QHBoxLayout()
        for tmp in ['Export selected JSON', 'Diff', 'Interrogate', 'Close']:
            button = QPushButton(tmp)
            button.setObjectName(tmp)
            footer_layout.addWidget(button)
            button.clicked.connect(self._footer_button_clicked)
        return footer_layout

    def _status_changed(self):
        if self.centralWidget():
            status_number = self.sender().objectName()
            status_str = self.sender().currentText()

            if status_str == 'Var. seed':
                search_str = 'Variation seed'
            elif status_str == 'Var. strength':
                search_str = 'Variation seed strength'
            elif status_str == 'Resize from':
                search_str = 'Seed resize from'
            elif status_str == 'Denoising':
                search_str = 'Denoising strength'
            else:
                search_str = status_str

            group_boxes = [widget for widget in self.centralWidget().findChildren(QGroupBox)]
            for index, group_box in enumerate(group_boxes):
                value = self.param_list[index].get(search_str, 'None')
                title_label = group_box.findChild(QLabel, status_number + '_title')
                value_label = group_box.findChild(QLabel, status_number + '_value')

                title_label.setText(status_str)
                value_label.setText(value)

    def _listview_clicked(self):
        name = self.sender().objectName()
        widget, number = name.split('_')
        index = int(number)

        if self.isActiveWindow():
            if widget == 'pixmap' and self.changed == 0:
                self.parent().root_tab.setCurrentIndex(index)
                self.parent().activateWindow()
                self.changed = 1
            elif widget == 'group' and self.changed == 0:
                if index in self.selected:
                    self.sender().setStyleSheet('')
                    self.selected.discard(index)
                else:
                    self.sender().setStyleSheet(style_sheet('group_selected'))
                    self.selected.add(index)
                self.changed = 1

            self.timer = QTimer()
            self.timer.timeout.connect(self._initialize_changed)
            self.timer.start(10)

    def _initialize_changed(self):
        self.changed = 0
        self.timer.stop()

    def _footer_button_clicked(self):
        where_from = self.sender().objectName()
        if where_from == 'Close':
            self.close()
        elif where_from == 'Export selected JSON':
            self.parent().export_json_selected(self.selected)
        elif where_from == 'Interrogate':
            self.parent().add_interrogate_tab(2, self.selected)
        elif where_from == 'Diff':
            if len(self.selected) == 2:
                params = [self.param_list[i] for i in self.selected]
                diff = DiffWindow(params, self)
                diff.show()
                diff.move_centre()

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())


def style_sheet(purpose: str):
    if purpose == 'extension_label':
        return 'border-radius: 5px ; ' \
               'border: 2px solid @@@ ; ' \
               'background-color: @@@ ; ' \
               'color: white ;'

    elif purpose == 'extension_label_available':
        return 'border-radius: 5px ; ' \
               'border: 2px solid palette(highlight) ; ' \
               'background-color: palette(highlight) ; ' \
               'color: white ;'

    elif purpose == 'extension_label_disabled':
        return 'border-radius: 5px ; ' \
               'border: 1px solid palette(shadow);'

    elif purpose == 'group_selected':
        return 'QGroupBox { border: 2px solid #86cecb; padding : 1px 0 0 0; }'
