# -*- coding: utf-8 -*-

from . import config
from .dialog import PixmapLabel
from .dialog import ClickableGroup
from .dialog import ProgressDialog
from .viewer import DiffWindow
from .widget import portrait_generator
from .widget import make_keybindings
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea
from PyQt6.QtWidgets import QWidget, QCheckBox, QComboBox, QLabel, QPushButton, QSpacerItem
from PyQt6.QtCore import Qt


class Listview(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.size = config.get('ListViewPixmapSize', 200)
        self.setWindowTitle('Listview')
        self.root_layout = None
        self.param_list = []
        self.status = ['Timestamp', 'Seed', 'Sampler', 'Steps', 'CFG scale', 'Model', 'VAE', 'Version']
        make_keybindings(self)

    def init_listview(self, param_list):
        self.setCentralWidget(None)
        self.param_list = param_list
        file_counts = len(param_list)

        progress = ProgressDialog()
        progress.setLabelText('Loading...')
        progress.setRange(0, len(self.param_list))

        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        root_widget = QWidget()
        self.root_layout = QVBoxLayout()

        for file_count in range(file_counts):
            group_box = self.groups(file_count)
            progress.update_value()
            self.root_layout.addWidget(group_box)

        groupbox_count = 4 if file_counts > 4 else file_counts
        root_widget.setLayout(self.root_layout)
        estimated_width = root_widget.sizeHint().width() + 50
        estimated_height = group_box.sizeHint().height() * groupbox_count + 50

        if estimated_height > 750:
            estimated_height = 750

        scroll_area.setWidget(root_widget)
        scroll_area.setMinimumWidth(estimated_width)
        scroll_area.setMinimumHeight(estimated_height)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        central_widget_layout.addLayout(self.header_section())
        central_widget_layout.addWidget(scroll_area)
        central_widget_layout.addLayout(self.footer_button())

        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)
        self.show()
        self.move_centre()

    def header_section(self):
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
            combo_box.setObjectName(str(index))
            combo_box.currentIndexChanged.connect(self.status_changed)
            header_layout.addWidget(combo_box, row, col)
            combo_box.addItems(combo_items)
            combo_box.setCurrentText(status)
            col += 1
            if col == 4:
                row += 1
                col = 0

        return header_layout

    def status_changed(self):
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

    def footer_button(self):
        footer_layout = QHBoxLayout()
        for tmp in ['Export selected JSON', 'Diff', 'Close']:
            button = QPushButton(tmp)
            button.setObjectName(tmp)
            footer_layout.addWidget(button)
            button.clicked.connect(self.footer_button_clicked)
        return footer_layout

    def footer_button_clicked(self):
        where_from = self.sender().objectName()
        if where_from == 'Close':
            self.close()
        elif where_from == 'Export selected JSON':
            self.check_group()
        elif where_from == 'Diff':
            self.check_group(True)

    def pixmap_label(self, index):
        filepath = self.param_list[index].get('Filepath', None)
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
        group = ClickableGroup()
        group.setObjectName('group_' + str(index))
        group.clicked.connect(self.group_clicked)
        group_layout = QHBoxLayout()
        status_label_layout = QGridLayout()
        pixmap_label = self.pixmap_label(index)

        for i, key in enumerate(self.status):

            item = self.param_list[index].get(key, 'None')
            title_label = QLabel(key)
            title_label.setObjectName(str(i) + '_title')
            status_label = QLabel(item)
            status_label.setObjectName(str(i) + '_value')
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
        addnet = any(key in v for v in self.param_list[index] for key in ['Lora', 'Textual inversion', 'Add network'])
        cfg = any(key in v for v in self.param_list[index] for key in ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler'])
        creation = 'T2I'

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
            elif status == 'Creation':
                style_sheet = "border-radius: 5px ;" \
                              "border: 2px solid @@@ ;" \
                              "background-color: @@@ ;" \
                              "color: white ;"
                if title == 'I2I' or title == 'inpaint':
                    style_sheet = style_sheet.replace('@@@', 'red')
                    extension_label.setStyleSheet(style_sheet)
                    if title == 'inpaint':
                        extension_label.setText('inpaint')
                    else:
                        extension_label.setText('img2img')
                elif title == 'T2I':
                    style_sheet = style_sheet.replace('@@@', 'palette(highlight)')
                    extension_label.setStyleSheet(style_sheet)
                    extension_label.setText('txt2img')
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
        group.setTitle(self.param_list[index].get('Filepath', 'None'))

        return group

    def pixmap_clicked(self):
        target_tab = self.sender().objectName()
        self.parent().root_tab.setCurrentIndex(int(target_tab))
        self.parent().activateWindow()

    def group_toggle(self):
        if self.sender().isChecked():
            self.sender().parent().setStyleSheet("QGroupBox {border: 2px solid #86cecb; padding : 1px 0 0 0; }")
        else:
            self.sender().parent().setStyleSheet("")

    def check_group(self, diff=False):
        indexes = []
        for widget in self.centralWidget().findChildren(QCheckBox):
            if widget.isChecked():
                index = widget.parent().objectName()
                indexes.append(int(index))
        if indexes:
            if diff and len(indexes) == 2:
                result = [self.param_list[i] for i in indexes]
                diff = DiffWindow(result, self)
                diff.show()
                diff.move_centre()
            elif not diff:
                self.parent().export_json_selected(indexes)

    def move_centre(self):
        if not self.parent() or not self.parent().isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = self.parent().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def group_clicked(self):
        pass
