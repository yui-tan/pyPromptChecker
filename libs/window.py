import os
import json
import sys
import csv
import libs.parser
import libs.decoder
import libs.configure
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog
from PyQt6.QtWidgets import QSplitter, QMainWindow, QGroupBox
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.setWindowTitle('PNG Prompt Data')
#        self.config = libs.configure.Config()
        self.models = model_hashes()
        self.params = []
        self.positive_for_copy = ''
        self.negative_for_copy = ''
        self.seed_for_copy = ''
        self.tab_index = 0
        self.init_ui(targets)

        window_width = 1024  # self.config.get_value('Window', 'WindowWidth')
        window_height = 920  # self.config.get_value('Window', 'WindowHeight')

        self.resize(window_width, window_height)
        self.center()

    def init_ui(self, targets):
        for filepath in targets:
            chunk_data = libs.decoder.decode_text_chunk(filepath, 1)
            parameters = libs.parser.parse_parameter(chunk_data, filepath, self.models)
            self.params.append(parameters)
        self.positive_for_copy = self.params[0].params.get('Positive')
        self.negative_for_copy = self.params[0].params.get('Negative')
        self.seed_for_copy = self.params[0].params.get('Seed')

        root_layout = QVBoxLayout()
        root_tab = QTabWidget()

        for tmp in self.params:
            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            label_group = QGroupBox()
            label_group_layout = QHBoxLayout()

            label_layout = make_label_layout(tmp)
            label_group_layout.addLayout(label_layout)
            label_group.setLayout(label_group_layout)
            tab_page_layout.addWidget(label_group)

            for i in range(8):
                inner_page = QWidget()
                if i == 0:
                    inner_page.setLayout(make_textbox_tab(tmp))
                    inner_tab.addTab(inner_page, 'Prompts')
                if i == 1 and (tmp.params.get('Hires upscale') or tmp.params.get(
                        'Face restoration') or tmp.params.get('Lora')):
                    inner_page.setLayout(make_hires_lora_tab(tmp))
                    inner_tab.addTab(inner_page, 'Hires / Loras')
                if i == 2 and tmp.params.get('Tiled diffusion'):
                    inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    inner_tab.addTab(inner_page, 'Tiled diffusion')
                if i == 3 and tmp.params.get('ControlNet'):
                    inner_page.setLayout(make_control_net_tab(tmp, 0))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 0-2')
                if i == 4 and tmp.params.get('ControlNet 3'):
                    inner_page.setLayout(make_control_net_tab(tmp, 3))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 3-5')
                if i == 5 and tmp.params.get('ControlNet 6'):
                    inner_page.setLayout(make_control_net_tab(tmp, 6))
                    inner_tab.addTab(inner_page, 'ControlNet Unit 6-8')
                if i == 6 and tmp.params.get('RP Active'):
                    inner_page.setLayout(make_regional_prompter_tab(tmp))
                    inner_tab.addTab(inner_page, 'Regional Prompter')
                if i == 7 and tmp.params.get('Dynamic thresholding enabled'):
                    inner_page.setLayout(make_other_tab(tmp))
                    inner_tab.addTab(inner_page, 'Other')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            root_tab.addTab(tab_page, tmp.params.get('Filename'))
            root_tab.currentChanged.connect(self.tab_changed)

        root_layout.addWidget(root_tab)

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

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().geometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def tab_changed(self, index):
        self.positive_for_copy = self.params[index].params.get('Positive')
        self.negative_for_copy = self.params[index].params.get('Negative')
        self.seed_for_copy = self.params[0].params.get('Seed')
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
                    dict_list.append(tmp.params)
                with open(filepath, 'w') as f:
                    json.dump(dict_list, f, sort_keys=True, indent=4, ensure_ascii=False)
        elif where_from == 'Reselect files':
            filepath = file_choose_dialog()[0]
            if filepath:
                self.params = []
                self.init_ui(filepath)


def result_window(target_data):
    app = QApplication(sys.argv)
    window = ResultWindow(target_data)
    window.show()
    sys.exit(app.exec())


def model_hashes():
    directory = os.path.dirname(__file__)
    filename = os.path.join(directory, 'model_list.csv')
    if os.path.exists(filename):
        with open(filename, encoding='utf8', newline='') as f:
            csvreader = csv.reader(f)
            model_list = [row for row in csvreader]
        return model_list
    else:
        return None


def make_label_layout(target):
    label_number = 0
    status = ['Filename',
              'Filepath',
              'Size',
              'Seed',
              'Sampler',
              'Eta',
              'Steps',
              'CFG scale',
              'Dynamic thresholding enabled',
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
    label_section_layout = QHBoxLayout()
    label_group_layout = QVBoxLayout()
    for tmp in status:
        item = target.params.get(tmp)
        if item:
            if tmp == 'Filepath':
                item = os.path.dirname(item)
            if tmp == 'Denoising strength' and target.params.get('Hires upscaler'):
                continue
            label_layout = QHBoxLayout()
            title = QLabel(tmp)
            value = QLabel(item)
            title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            size_policy_title = title.sizePolicy()
            size_policy_value = value.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(2)
            title.setSizePolicy(size_policy_title)
            value.setSizePolicy(size_policy_value)
            label_layout.addWidget(title)
            label_layout.addWidget(value)
            label_group_layout.addLayout(label_layout)
            label_number = label_number + 1
            if tmp == 'Lora':
                title.setText('Lora in prompt')
            elif tmp == 'Hires upscaler':
                title.setText('Hires.fix')
                value.setText('True')
            elif tmp == 'Dynamic thresholding enabled':
                title.setText('CFG scale fix')
    if label_number < 15:
        for i in range(15 - label_number):
            margin_label = QLabel()
            label_group_layout.addWidget(margin_label)
    filepath = target.params.get('Filepath')
    pixmap_label = make_pixmap_label(filepath)
    label_section_layout.addWidget(pixmap_label)
    label_section_layout.addLayout(label_group_layout)

    return label_section_layout


def make_pixmap_label(filepath):
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    pixmap_label = QLabel()
    pixmap_label.setPixmap(pixmap)
    pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return pixmap_label


def make_textbox_tab(target):
    textbox_tab_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)
    positive_text = target.params.get('Positive')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    negative_text = target.params.get('Negative')
    negative_prompt = QTextEdit()
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_tab_layout.addWidget(splitter)

    return textbox_tab_layout


def make_hires_lora_tab(target):
    tab_layout = QHBoxLayout()
    hires_group = make_hires_group(target)
    tab_layout.addLayout(hires_group, 3)
    lora_group = make_lora_section(target)
    tab_layout.addWidget(lora_group, 3)
    addnet_group = make_addnet_section(target)
    tab_layout.addWidget(addnet_group, 4)
    return tab_layout


def make_hires_group(target):
    hires = ['Hires upscaler', 'Hires upscale', 'Hires resize', 'Hires steps', 'Denoising strength']
    hires_group_layout = QVBoxLayout()
    hires_section = QGroupBox()
    hires_section.setTitle('Hires.fix')
    hires_section_layout = QVBoxLayout()
    for tmp in hires:
        label_layout = QHBoxLayout()
        item = target.params.get(tmp)
        if not item:
            if tmp == 'Hires upscaler':
                hires_section.setDisabled(True)
            item = 'None'
        tmp = tmp.replace('Hires ', '').capitalize().replace('strength', '')
        title = QLabel(tmp)
        value = QLabel(item)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(3)
        size_policy_value.setHorizontalStretch(7)
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
    item = target.params.get(name)
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
    cnt = len(target.params)
    lora_section = QGroupBox()
    loras = target.params.get('Lora')
    section_layout = QVBoxLayout()
    if loras:
        lora_section.setTitle('Lora in prompt : ' + loras)
        for i in range(cnt):
            key = 'Lora ' + str(i)
            item = target.params.get(key)
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
                section_layout.addLayout(label_layout)
                label_cnt = label_cnt + 1
    else:
        lora_section.setDisabled(True)
        lora_section.setTitle('Lora : 0')
    lora_section.setLayout(section_layout)
    return lora_section


def make_addnet_section(target):
    status = ['Module', 'Model', 'Weight A']
    addnet_section = QGroupBox()
    section_layout = QVBoxLayout()
    addnet_section.setTitle('Additional Networks')
    addnet = target.params.get('AddNet Enabled')
    if not addnet:
        addnet_section.setDisabled(True)
    for i in range(1, 6):
        for tmp in status:
            label_layout = QHBoxLayout()
            key = 'AddNet ' + tmp + ' ' + str(i)
            item = target.params.get(key)
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
                item_2 = float(target.params.get('AddNet Weight B ' + str(i)))
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
    tab_layout = QHBoxLayout()
    tiled_diffusion_section = QVBoxLayout()
    tiled_diffusion_basic_info = make_tiled_diffusion_group(target)
    noise_inversion_info = make_noise_inversion_group(target)
    region_control_info = region_control_group(target)

    tiled_diffusion_section.addWidget(tiled_diffusion_basic_info)
    tiled_diffusion_section.addWidget(noise_inversion_info)

    tab_layout.addLayout(tiled_diffusion_section, 1)
    tab_layout.addWidget(region_control_info, 1)
    return tab_layout


def make_tiled_diffusion_group(target):
    status = ['Method',
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
    section.setLayout(label_maker(status, target, 1, 2))
    return section


def make_noise_inversion_group(target):
    status = ['Noise inversion Kernel size',
              'Noise inversion Renoise strength',
              'Noise inversion Retouch',
              'Noise inversion Steps'
              ]
    section = QGroupBox()
    section.setTitle('Noise inversion')
    if not target.params.get('Noise inversion'):
        section.setDisabled(True)
    status = [[value, value.replace('Noise inversion ', '')] for value in status]
    section.setLayout(label_maker(status, target, 1, 2))
    return section


def region_control_group(target):
    status = ['blend mode',
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
        check = target.params.get(region_number + ' enable')
        if check or i == 0:
            page = QWidget()
            region_control_section_layout = QVBoxLayout()
            for tmp in status:
                label_layout = QHBoxLayout()
                key = region_number + ' ' + tmp
                item = target.params.get(key)
                title = tmp.replace('neg', 'negative').capitalize()
                if not item:
                    item = 'None'
                if title == 'W':
                    title = 'Width'
                elif title == 'H':
                    title = 'Height'
                if 'prompt' in tmp:
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
    status = [['model', 'Model'],
              ['control mode', 'Control mode'],
              ['pixel perfect', 'Pixel perfect'],
              ['preprocessor', 'Preprocessor'],
              ['resize mode', 'Resize mode'],
              ['starting/ending', 'Starting/ending'],
              ['weight', 'Weight'],
              ['preprocessor params', 'Preproc. params'],
              ]
    for i in range(starts, 3):
        control_net_enable = target.params.get('ControlNet ' + str(i))
        status = [['ControlNet ' + str(i) + ' ' + value[0], value[1]] for value in status]
        section = QGroupBox()
        section.setTitle('ControlNet Unit ' + str(i))
        if not control_net_enable:
            section.setDisabled(True)
        section.setLayout(label_maker(status, target, 4, 6))
        page_layout.addWidget(section)
    return page_layout


def make_regional_prompter_tab(target, scale=500):
    filepath = target.params.get('Filepath')
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(scale, scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

    regional_prompter_group = QHBoxLayout()
    regional_prompter_group.addWidget(make_regional_prompter_status_section(target), 1)

    ratio_pixmap_label = QLabel()
    str_ratios = target.params.get('RP Ratios')
    ratio_mode = target.params.get('RP Matrix submode')
    main, sub = regional_prompter_ratio_check(str_ratios, ratio_mode)
    if main and sub:
        pixmap = make_regional_prompter_pixmap(pixmap, ratio_mode, main, sub)
        ratio_pixmap_label.setPixmap(pixmap)
    else:
        ratio_pixmap_label.setText("Couldn't analyze ratio strings")
    ratio_pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    ratio_strings = '(' + str_ratios.replace(' ', '') + ')'

    ratio_strings_section = QGroupBox()
    ratio_strings_section_layout = QVBoxLayout()
    ratio_strings_section.setTitle('Regional Prompter Ratios: ' + ratio_mode + ' ' + ratio_strings)

    ratio_strings_section_layout.addWidget(ratio_pixmap_label)
    ratio_strings_section.setLayout(ratio_strings_section_layout)
    regional_prompter_group.addWidget(ratio_strings_section, 2)

    return regional_prompter_group


def make_regional_prompter_status_section(target):
    status = [['RP Calc Mode', 'Generation Mode'],
              ['RP Base Ratios', 'Base prompt ratio'],
              ['RP Use Base', 'Use base prompt'],
              ['RP Use Common', 'Use common prompt'],
              ['RP Use Ncommon', 'Use negative prompt'],
              ['RP Divide mode', 'Divide mode'],
              ['RP Mask submode', 'Mask submode'],
              ['RP Prompt submode', 'Prompt submode'],
              ['RP Change AND', 'Change "AND" to "BREAK"'],
              ['RP LoRA Neg U Ratios', 'Lora negative UNet Ratio'],
              ['RP LoRA Neg Te Ratios', 'Lora negative TEnc Ratio'],
              ['RP threshold', 'Threshold']]
    status_section = QGroupBox()
    status_section.setLayout(label_maker(status, target, 6, 4))
    status_section.setTitle('Status')
    return status_section


def make_regional_prompter_pixmap(pixmap, divide_mode, main_ratio, sub_ratio):
    divide_sum = sum(main_ratio)

    paint_area = QPainter()
    paint_area.begin(pixmap)
    paint_area.drawPixmap(0, 0, pixmap)
    paint_area.setPen(QColor(255, 255, 255))
    paint_area.setBrush(QColor(255, 255, 255))
    painted_pos_y = 0
    painted_pos_x = 0

    if divide_mode == 'Horizontal':
        for index, ratio in enumerate(main_ratio):
            height_by_ratio = int((pixmap.height() / divide_sum) * ratio)
            start_draw_pos_y = painted_pos_y + height_by_ratio
            paint_area.drawRect(0, start_draw_pos_y, pixmap.width(), 2)
            if sub_ratio[index] and len(sub_ratio[index]) > 1:
                sub_divide_sum = sum(sub_ratio[index])
                painted_pos_x = 0
                for tmp in sub_ratio[index]:
                    width_by_sub_ratio = int((pixmap.width() / sub_divide_sum) * tmp)
                    start_draw_pos_x = painted_pos_x + width_by_sub_ratio
                    paint_area.drawRect(start_draw_pos_x, painted_pos_y, 2, height_by_ratio)
                    painted_pos_x = start_draw_pos_x
            painted_pos_y = start_draw_pos_y
    elif divide_mode == 'Vertical':
        for index, ratio in enumerate(main_ratio):
            width_by_ratio = int((pixmap.width() / divide_sum) * ratio)
            start_draw_pos_x = painted_pos_x + width_by_ratio
            paint_area.drawRect(start_draw_pos_x, 0, 2, pixmap.height())
            if sub_ratio[index] and len(sub_ratio[index]) > 1:
                sub_divide_sum = sum(sub_ratio[index])
                painted_pos_y = 0
                for tmp in sub_ratio[index]:
                    height_by_sub_ratio = int((pixmap.height() / sub_divide_sum) * tmp)
                    start_draw_pos_y = painted_pos_y + height_by_sub_ratio
                    paint_area.drawRect(painted_pos_x, start_draw_pos_y, width_by_ratio, 2)
                    painted_pos_y = start_draw_pos_y
            painted_pos_x = start_draw_pos_x

    paint_area.end()

    return pixmap


def regional_prompter_ratio_check(str_ratio, divide_mode):
    result = True
    main_ratio = []
    sub_ratio = []
    major_splitter = ';'
    minor_splitter = ','
    if divide_mode == 'Vertical':
        major_splitter = minor_splitter
        minor_splitter = ';'

    for tmp in str_ratio.split(major_splitter):
        ratio = tmp.split(minor_splitter)
        try:
            main_ratio.append(int(ratio[0]))
            sub_ratio.append([int(number) for number in ratio[1:]])
        except ValueError:
            result = False
            break

    if not result:
        return None, None
    else:
        return main_ratio, sub_ratio


def make_other_tab(target):
    page_layout = QHBoxLayout()
    page_layout.addWidget(dynamic_thresholding_section(target))
    for i in range(2):
        page_layout.addWidget(make_dummy_section(7))
    return page_layout


def dynamic_thresholding_section(target):
    status = ['CFG mode',
              'CFG scale minimum',
              'Mimic mode',
              'Mimic scale',
              'Mimic scale minimum',
              'Scheduler value',
              'Threshold percentile'
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 6, 4))
    section.setTitle('Dynamic thresholding (CFG scale fix)')
    return section


def label_maker(status, target, stretch_title, stretch_value, selectable=False, remove_if_none=False):
    section_layout = QVBoxLayout()
    for tmp in status:
        label_layout = QHBoxLayout()
        if isinstance(tmp, list):
            item = target.params.get(tmp[0])
            if 'ControlNet' in tmp[0] and 'model' in tmp[0] and item:
                item = item.replace(' ', '\n')
            tmp = tmp[1]
        else:
            item = target.params.get(tmp)
        if not item and remove_if_none:
            continue
        elif not item:
            item = 'None'
            if tmp == 'Keep input size':
                item = 'False'
        title = QLabel(tmp)
        value = QLabel(item)
        if selectable:
            title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(stretch_title)
        size_policy_value.setHorizontalStretch(stretch_value)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        label_layout.addWidget(title)
        label_layout.addWidget(value)
        section_layout.addLayout(label_layout)
    return section_layout


def make_dummy_section(num):
    section = QGroupBox()
    section_layout = QVBoxLayout()
    for i in range(num):
        title = QLabel()
        section_layout.addWidget(title)
    section.setLayout(section_layout)
    section.setTitle('Dummy')
    section.setDisabled(True)
    return section


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


def file_choose_dialog(where=False):
    if where:
        app = QApplication(sys.argv)
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


def directory_choose_dialog(where=False):
    if where:
        app = QApplication(sys.argv)
    caption = 'Select Directory'
    default_dir = os.path.expanduser('~')
    directory = QFileDialog.getExistingDirectory(
        None,
        caption,
        default_dir,
    )
    return directory
