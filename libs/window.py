import os
import json
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog
from PyQt6.QtWidgets import QSplitter, QMainWindow, QGroupBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ResultWindow(QMainWindow):
    def __init__(self, target_data):
        super().__init__()

        self.Properties = ['Filename',
                           'Filepath',
                           'Size',
                           'Seed',
                           'Sampler',
                           'Steps',
                           'CFG scale',
                           'Model',
                           'Variation seed',
                           'Variation seed strength',
                           'Denoising strength',
                           'Clip skip',
                           'Lora',
                           'Hires upscaler',
                           'ControlNet',
                           'ENSD',
                           'Version']
        self.setWindowTitle('PNG Prompt Data')
        self.params = target_data
        self.positive_for_copy = self.params[0].dictionary_get('Positive')
        self.negative_for_copy = self.params[0].dictionary_get('Negative')
        self.seed_for_copy = self.params[0].dictionary_get('Seed')
        self.tab_index = 0
        window_width = 1024
        window_height = 920

        root_layout = QVBoxLayout()
        self.root_tab = QTabWidget()

        for tmp in self.params:
            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            label_group = QGroupBox()
            label_group_layout = QHBoxLayout()

            label_layout = make_label_layout(self, tmp)
            label_group_layout.addLayout(label_layout)
            label_group.setLayout(label_group_layout)
            tab_page_layout.addWidget(label_group)

            for i in range(5):
                inner_page = QWidget()
                if i == 0:
                    inner_page.setLayout(make_page_layout(tmp))
                    inner_tab.addTab(inner_page, 'Prompts')
                if i == 1 and (tmp.dictionary_get('Hires upscale') or tmp.dictionary_get(
                        'Face restoration') or tmp.dictionary_get('Lora')):
                    inner_page.setLayout(make_hires_lora_tab(tmp))
                    inner_tab.addTab(inner_page, 'Hires / Loras')
                if i == 2 and tmp.dictionary_get('Tiled diffusion'):
                    inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    inner_tab.addTab(inner_page, 'Tiled diffusion')
                if i == 3 and tmp.dictionary_get('ControlNet'):
                    inner_page.setLayout(make_control_net_tab(tmp, 0))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 0-2')
                if i == 4 and tmp.dictionary_get('ControlNet 3'):
                    inner_page.setLayout(make_control_net_tab(tmp, 3))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 3-5')
                if i == 5 and tmp.dictionary_get('ControlNet 6'):
                    inner_page.setLayout(make_control_net_tab(tmp, 6))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 6-8')
            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            self.root_tab.addTab(tab_page, tmp.dictionary_get('Filename'))
            self.root_tab.currentChanged.connect(self.tab_changed)

        root_layout.addWidget(self.root_tab)

        button_layout = QHBoxLayout()
        button_text = ['Positive to Clipboard',
                       'Negative to Clipboard',
                       'Seed to Clipboard',
                       'Export JSON (This image)',
                       'Export JSON (All images)',
                       'Reselect files']
        for tmp in button_text:
            copy_button = QPushButton(tmp)
            button_layout.addWidget(copy_button)
            copy_button.clicked.connect(self.button_clicked)

        root_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(root_layout)
        self.setCentralWidget(central_widget)

        self.resize(window_width, window_height)
        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().geometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def tab_changed(self, index):
        self.positive_for_copy = self.params[index].dictionary_get('Positive')
        self.negative_for_copy = self.params[index].dictionary_get('Negative')
        self.seed_for_copy = self.params[0].dictionary_get('Seed')
        self.tab_index = index

    def button_clicked(self):
        where_from = self.sender().text()
        clipboard = QApplication.clipboard()
        if where_from == 'Positive to Clipboard':
            if self.positive_for_copy:
                clipboard.setText(self.positive_for_copy)
        elif where_from == 'Negative to Clipboard':
            if self.negative_for_copy:
                clipboard.setText(self.negative_for_copy)
        elif where_from == 'Seed to Clipboard':
            if self.seed_for_copy:
                clipboard.setText(self.seed_for_copy)
        elif where_from == 'Export JSON (This image)':
            data = self.params[self.tab_index]
            filepath = savefile_choose_dialog()
            data.json_export(filepath)
        elif where_from == 'Export JSON (All images)':
            filepath = savefile_choose_dialog(True)
            if filepath:
                dict_list = []
                for tmp in self.params:
                    dict_list.append(tmp.all_dictionary())
                with open(filepath, 'w') as f:
                    json.dump(dict_list, f, sort_keys=True, indent=4, ensure_ascii=False)
        elif where_from == 'Reselect files':
            pass
        #    sys.stdout.flush()
        #    os.execv(sys.argv[0], sys.argv)


def make_page_layout(target_data):
    textbox_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)
    positive_text = target_data.dictionary_get('Positive')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    negative_text = target_data.dictionary_get('Negative')
    negative_prompt = QTextEdit()
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_layout.addWidget(splitter)

    return textbox_layout


def make_label_layout(layout, data):
    label_number = 0
    upper_label_layout = QHBoxLayout()
    label_layout = QVBoxLayout()
    for tmp in layout.Properties:
        item = data.dictionary_get(tmp)
        if item:
            if tmp == 'Filepath':
                item = os.path.dirname(item)
            status_layout = QHBoxLayout()
            title = QLabel(tmp)
            value = QLabel(item)
            size_policy_title = title.sizePolicy()
            size_policy_value = value.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(2)
            title.setSizePolicy(size_policy_title)
            value.setSizePolicy(size_policy_value)
            status_layout.addWidget(title)
            status_layout.addWidget(value)
            label_layout.addLayout(status_layout)
            label_number = label_number + 1
            if tmp == 'Lora':
                title.setText('Lora in prompt')
            elif tmp == 'Hires upscaler':
                title.setText('Hires.fix')
                value.setText('True')
    if label_number < 15:
        for i in range(15 - label_number):
            margin = QLabel()
            label_layout.addWidget(margin)
    filepath = data.dictionary_get('Filepath')
    pixmap = make_pixmap_label(filepath)
    upper_label_layout.addWidget(pixmap)
    upper_label_layout.addLayout(label_layout)

    return upper_label_layout


def make_hires_lora_tab(target):
    page_layout = QHBoxLayout()
    hires_group = make_hires_group(target)
    page_layout.addLayout(hires_group, 2)
    lora_group = make_lora_section(target)
    page_layout.addWidget(lora_group, 3)
    addnet_group = make_addnet_section(target)
    page_layout.addWidget(addnet_group, 3)
    return page_layout


def make_hires_group(target):
    hires = ['Hires upscaler', 'Hires upscale', 'Hires resize', 'Hires steps', 'Denoising strength']
    hires_group_layout = QVBoxLayout()
    hires_section = QGroupBox()
    hires_section.setTitle('Hires.fix')
    hires_section_layout = QVBoxLayout()
    for tmp in hires:
        label_layout = QHBoxLayout()
        item = target.dictionary_get(tmp)
        if not item:
            if tmp == 'Hires upscaler':
                hires_section.setDisabled(True)
            item = 'None'
        title = QLabel(tmp)
        value = QLabel(item)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(2)
        size_policy_value.setHorizontalStretch(1)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        label_layout.addWidget(title)
        label_layout.addWidget(value)
        hires_section_layout.addLayout(label_layout)
    hires_section.setLayout(hires_section_layout)

    label_layout = QHBoxLayout()
    face_section = QGroupBox()
    face_section.setTitle('Face restoration')
    name = 'Face restoration'
    item = target.dictionary_get(name)
    if not item:
        face_section.setDisabled(True)
        item = 'None'
    title = QLabel(name)
    value = QLabel(item)
    size_policy_title = title.sizePolicy()
    size_policy_value = value.sizePolicy()
    size_policy_title.setHorizontalStretch(2)
    size_policy_value.setHorizontalStretch(1)
    title.setSizePolicy(size_policy_title)
    value.setSizePolicy(size_policy_value)
    label_layout.addWidget(title)
    label_layout.addWidget(value)
    face_section.setLayout(label_layout)

    hires_group_layout.addWidget(hires_section, 2)
    hires_group_layout.addWidget(face_section, 1)
    return hires_group_layout


def make_lora_section(target):
    label_cnt = 0
    cnt = target.dictionary_length()
    lora_section = QGroupBox()
    loras = target.dictionary_get('Lora')
    group_layout = QVBoxLayout()
    if loras:
        lora_section.setTitle('Lora in prompt : ' + loras)
        for i in range(cnt):
            key = 'Lora ' + str(i)
            item = target.dictionary_get(key)
            if item or label_cnt < 10:
                label_layout = QHBoxLayout()
                if not item:
                    key = ''
                title = QLabel(key)
                value = QLabel(item)
                size_policy_title = title.sizePolicy()
                size_policy_value = value.sizePolicy()
                size_policy_title.setHorizontalStretch(1)
                size_policy_value.setHorizontalStretch(2)
                title.setSizePolicy(size_policy_title)
                value.setSizePolicy(size_policy_value)
                label_layout.addWidget(title)
                label_layout.addWidget(value)
                group_layout.addLayout(label_layout)
                label_cnt = label_cnt + 1
    else:
        lora_section.setDisabled(True)
        lora_section.setTitle('Lora : 0')
    lora_section.setLayout(group_layout)
    return lora_section


def make_addnet_section(target):
    status = ['Module', 'Model', 'Weight A']
    addnet_section = QGroupBox()
    section_layout = QVBoxLayout()
    addnet_section.setTitle('Additional Networks')
    addnet = target.dictionary_get('AddNet Enabled')
    if not addnet:
        addnet_section.setDisabled(True)
    for i in range(1, 6):
        for tmp in status:
            label_layout = QHBoxLayout()
            key = 'AddNet ' + tmp + ' ' + str(i)
            item = target.dictionary_get(key)
            if tmp == 'Module' and item:
                title = QLabel('Module ' + str(i))
                value = QLabel(item)
            elif tmp == 'Model' and item:
                title = QLabel('Model')
                item = item.replace('(', '[').replace(')', ']')
                value = QLabel(item)
            elif tmp == 'Weight A' and item:
                title = QLabel('UNet / TEnc')
                item = float(item)
                item_2 = float(target.dictionary_get('AddNet Weight B ' + str(i)))
                item = str(item) + ' / ' + str(item_2)
                value = QLabel(item)
            else:
                title = QLabel()
                value = QLabel()
            size_policy_title = title.sizePolicy()
            size_policy_value = value.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(3)
            title.setSizePolicy(size_policy_title)
            value.setSizePolicy(size_policy_value)
            label_layout.addWidget(title)
            label_layout.addWidget(value)
            section_layout.addLayout(label_layout)
    addnet_section.setLayout(section_layout)
    return addnet_section


def make_tiled_diffusion_tab(target):
    page_layout = QHBoxLayout()
    tiled_diffusion_section = QVBoxLayout()
    tiled_diffusion_basic_info = make_tiled_diffusion_group(target)
    noise_inversion_info = make_noise_inversion_group(target)
    region_control_info = region_control_group(target)

    tiled_diffusion_section.addWidget(tiled_diffusion_basic_info)
    tiled_diffusion_section.addWidget(noise_inversion_info)

    page_layout.addLayout(tiled_diffusion_section, 1)
    page_layout.addWidget(region_control_info, 1)
    return page_layout


def make_tiled_diffusion_group(target):
    status_data = ['Method',
                   'Keep input size',
                   'Tile batch size',
                   'Tile width',
                   'Tile height',
                   'Tile Overlap',
                   'Upscaler',
                   'Upscale factor'
                   ]
    section = QGroupBox()
    section.setTitle('Tiled diffusion')
    section_layout = QVBoxLayout()
    for status in status_data:
        item = target.dictionary_get(status)
        if not item:
            if status == 'Keep input size':
                item = 'False'
            elif status == 'Upscaler' or status == 'Upscale factor':
                item = 'None'
        status_layout = QHBoxLayout()
        title = QLabel(status)
        value = QLabel(item)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(1)
        size_policy_value.setHorizontalStretch(2)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        status_layout.addWidget(title)
        status_layout.addWidget(value)
        section_layout.addLayout(status_layout)
    section.setLayout(section_layout)
    return section


def make_noise_inversion_group(target):
    status_data = ['Noise inversion Kernel size',
                   'Noise inversion Renoise strength',
                   'Noise inversion Retouch',
                   'Noise inversion Steps']
    section = QGroupBox()
    section.setTitle('Noise inversion')
    if not target.dictionary_get('Noise inversion'):
        section.setDisabled(True)
    section_layout = QVBoxLayout()
    for status in status_data:
        item = target.dictionary_get(status)
        status = status.replace('Noise inversion ', '')
        if not item:
            item = 'None'
        status_layout = QHBoxLayout()
        title = QLabel(status)
        value = QLabel(item)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(1)
        size_policy_value.setHorizontalStretch(2)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        status_layout.addWidget(title)
        status_layout.addWidget(value)
        section_layout.addLayout(status_layout)
    section.setLayout(section_layout)
    return section


def region_control_group(target):
    flag = False
    status_data = ['blend mode',
                   'feather ratio',
                   'w',
                   'h',
                   'x',
                   'y',
                   'seed',
                   'prompt',
                   'neg prompt'
                   ]
    region_control_tab = QTabWidget()
    for i in range(8):
        region_number = 'Region ' + str(i + 1)
        check = target.dictionary_get(region_number + ' enable')
        if check or i == 0:
            page = QWidget()
            region_control_section_layout = QVBoxLayout()
            for status in status_data:
                label_layout = QHBoxLayout()
                key = region_number + ' ' + status
                item = target.dictionary_get(key)
                title = status.replace('neg', 'negative').capitalize()
                if not item:
                    item = 'None'
                if title == 'W':
                    title = 'Width'
                elif title == 'H':
                    title = 'Height'
                if 'prompt' in status:
                    status_label = QTextEdit()
                    status_label.setText(item)
                    label_layout.addWidget(status_label)
                else:
                    status_label = QLabel(title)
                    values_label = QLabel(item)
                    label_layout.addWidget(status_label)
                    label_layout.addWidget(values_label)
                region_control_section_layout.addLayout(label_layout)
            page.setLayout(region_control_section_layout)
            region_control_tab.addTab(page, region_number)
            if not check:
                region_control_tab.setDisabled(True)
    return region_control_tab


def make_control_net_tab(target, starts):
    page_layout = QHBoxLayout()
    status_data = ['model',
                   'control mode',
                   'pixel perfect',
                   'preprocessor',
                   'resize mode',
                   'starting/ending',
                   'weight',
                   'preprocessor params']
    for i in range(starts, 3):
        control_net_enable = target.dictionary_get('ControlNet ' + str(i))
        section = QGroupBox()
        section_layout = QVBoxLayout()
        section.setTitle('ControlNet Unit ' + str(i))
        if not control_net_enable:
            section.setDisabled(True)
        for tmp in status_data:
            label_layout = QHBoxLayout()
            key = 'ControlNet ' + str(i) + ' ' + tmp
            item = target.dictionary_get(key)
            key = tmp.capitalize()
            if key == 'Starting/ending':
                key = 'Starting/Ending'
            elif key == 'Preprocessor params':
                key = 'Preproc. params'
            if not item:
                item = 'None'
            elif key == 'Model':
                item = item.replace(' ', '\n')
            title = QLabel(key)
            value = QLabel(item)
            size_policy_title = title.sizePolicy()
            size_policy_value = value.sizePolicy()
            size_policy_title.setHorizontalStretch(4)
            size_policy_value.setHorizontalStretch(6)
            title.setSizePolicy(size_policy_title)
            value.setSizePolicy(size_policy_value)
            label_layout.addWidget(title)
            label_layout.addWidget(value)
            section_layout.addLayout(label_layout)
        section.setLayout(section_layout)
        page_layout.addWidget(section)
    return page_layout


def make_regional_prompter_tab():
    pass


def make_pixmap_label(filepath):
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    image_label = QLabel()
    image_label.setPixmap(pixmap)
    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return image_label


def savefile_choose_dialog(all_images=False):
    caption = 'Save File'
    path = os.path.expanduser('~')
    default_filename = os.path.join(path, 'parameters.json')
    if all_images:
        default_filename = os.path.join(path, 'all_parameters.json')
    file_filter = 'JSON Files(*.json)'
    select_filter = ''
    filename, _ = QFileDialog.getSaveFileName(
        None,
        caption,
        default_filename,
        file_filter,
        select_filter
    )
    return filename


def file_choose_dialog():
    caption = 'Select Files'
    default_dir = os.path.expanduser('~')
    file_filter = 'PNG Images(*.png)'
    select_filter = ''
    filenames = QFileDialog.getOpenFileNames(
        None,
        caption,
        default_dir,
        file_filter,
        select_filter
    )
    return filenames
