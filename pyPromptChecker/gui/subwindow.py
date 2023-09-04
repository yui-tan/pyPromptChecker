# -*- coding: utf-8 -*-

from .dialog import ProgressDialog
from .dialog import PixmapLabel
from functools import lru_cache
from PyQt6.QtWidgets import QMainWindow, QApplication, QGridLayout, QGroupBox, QCheckBox, QScrollArea
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QSpacerItem
from PyQt6.QtGui import QPixmap, QImageReader
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

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        root_widget = QWidget()
        root_layout = QVBoxLayout()

        for i in range(file_counts):
            group_box = self.groups(i)
            root_layout.addWidget(group_box)

        root_widget.setLayout(root_layout)
        estimated_width = root_widget.sizeHint().width() + 50

        scroll_area.setWidget(root_widget)
        scroll_area.setMinimumWidth(estimated_width)

        self.setCentralWidget(scroll_area)
        self.show()
        move_centre(self, self.parent())

    def pixmap_labels(self, index):
        filepath = self.dictionary_list[index].get('Filepath', None)
        if filepath:
            pixmap = portrait_generator(filepath)
            pixmap_label = QLabel()
            pixmap_label.setMinimumSize(150, 150)
            pixmap_label.setMaximumSize(150, 150)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap_label.setPixmap(pixmap)
            return pixmap_label
        else:
            return None

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

        for condition_list in [['Extras', 'Extras' in self.dictionary_list[index]],
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
            else:
                extension_label.setStyleSheet("border-radius: 5px ;"
                                              "border: 2px solid palette(highlight) ;"
                                              "background-color: palette(highlight) ;"
                                              "color: palette(highlightedText) ;")
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
