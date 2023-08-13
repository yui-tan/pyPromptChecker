import datetime
import os
import sys
import pyPromptChecker.lib.decoder
import pyPromptChecker.lib.parser
import pyPromptChecker.lib.configure
import pyPromptChecker.lib.io
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtWidgets import QSplitter, QMainWindow, QGroupBox, QScrollArea, QProgressDialog
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, pyqtSignal


class PixmapLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(PixmapLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return QLabel.mousePressEvent(self, event)


class ProgressDialog(QProgressDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progress")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setCancelButton(None)
        self.setMinimumDuration(0)
        self.setValue(0)
        self.now = 0
        move_center(self, parent)

    def update_value(self):
        now = self.now + 1
        self.setValue(now)
        self.now = now


class ImageWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.screen = QApplication.primaryScreen()
        self.filepath = ''
        self.max_screen = self.screen.availableGeometry()
        self.screen_center = self.screen.geometry().center()

    def init_ui(self):
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
        label.setScaledContents(True)

        label.clicked.connect(self.clicked)

        self.setCentralWidget(label)
        self.show()
        move_center(self)

    def clicked(self):
        self.close()


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.root_tab = None
        self.progress_bar = None
        self.progress_bar_enable = False
        self.config = pyPromptChecker.lib.configure.Configure()
        self.setWindowTitle('PNG Prompt Data')
        self.models = pyPromptChecker.lib.io.import_model_list(self.config.get_option('ModelList'))
        self.params = []
        self.positive_for_copy = ''
        self.negative_for_copy = ''
        self.seed_for_copy = ''
        self.tab_index = 0
        self.init_ui(targets)
        self.image_window = ImageWindow()
        self.tab_max_count = 0

        size_hint_width = self.sizeHint().width()
        size_hint_height = self.sizeHint().height()
        max_width = self.config.get_option('MaxWindowWidth')
        max_height = self.config.get_option('MaxWindowHeight')

        window_width = size_hint_width if max_width > size_hint_width else max_width
        window_height = size_hint_height if max_height > size_hint_height else max_height
        self.resize(window_width, window_height)
        self.center()

    def init_ui(self, targets):
        self.progress_bar_enable = True if len(targets) > 20 else False
        ignore = self.config.get_option('IgnoreIfDataIsNotEmbedded')
        total = len(targets)
        valid_total = total
        image_count = 1

        if self.progress_bar_enable:
            self.progress_bar = ProgressDialog(self)
            self.progress_bar.setRange(0, total * 2)
            self.progress_bar.update_value()
            self.progress_bar.setLabelText('Extracting PNG Chunk...')

        for filepath in targets:
            chunk_data = pyPromptChecker.lib.decoder.chunk_text_extractor(filepath, 1)
            parameters = pyPromptChecker.lib.parser.parse_parameter(chunk_data, filepath, self.models)
            if parameters.params['Positive'] == 'This file has no embedded data' and ignore:
                valid_total = valid_total - 1
                continue
            self.params.append(parameters)
            if self.progress_bar_enable:
                self.progress_bar.update_value()

        if valid_total == 0:
            show_messagebox('Warning', 'There is no embedded data to parse.')
            sys.exit()

        if self.progress_bar_enable:
            self.progress_bar.setLabelText('Formatting prompt data...')

        self.positive_for_copy = self.params[0].params.get('Positive')
        self.negative_for_copy = self.params[0].params.get('Negative')
        self.seed_for_copy = self.params[0].params.get('Seed')

        root_layout = QVBoxLayout()
        self.root_tab = QTabWidget()

        for tmp in self.params:

            if self.progress_bar_enable:
                self.progress_bar.update_value()
            if valid_total > 1:
                tmp.params['File count'] = str(image_count) + ' / ' + str(valid_total)

            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            main_section = QGroupBox()
            main_section_layout = QHBoxLayout()

            pixmap_scale = self.config.get_option('PixmapSize')
            main_label_layout = make_main_section(tmp, pixmap_scale)
            main_section_layout.addLayout(main_label_layout)
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)
            pixmap_label = main_section.findChild(PixmapLabel, 'Pixmap')
            pixmap_label.clicked.connect(self.pixmap_clicked)
            for button in ['Favourite', 'Move to', 'Delete']:
                managing_button = main_section.findChild(QPushButton, button)
                managing_button.clicked.connect(self.managing_button_clicked)

            hires_tab = ['Hires upscaler', 'Face restoration', 'Dynamic thresholding enabled']
            lora_tab = ['Lora', 'AddNet Enabled']

            tabs = [['Prompts', True, True],
                    ['Hires.fix / CFG scale fix',
                     any(key in v for v in tmp.params for key in hires_tab),
                     self.config.get_option('HiresCfg')],
                    ['Lora / Add networks',
                     any(key in v for v in tmp.params for key in lora_tab),
                     self.config.get_option('LoraAddNet')],
                    ['Tiled diffusion',
                     'Tiled diffusion' in tmp.params,
                     self.config.get_option('TiledDiffusion')],
                    ['Control net',
                     'ControlNet' in tmp.params,
                     self.config.get_option('ControlNet')],
                    ['Regional prompter',
                     'RP Active' in tmp.params,
                     self.config.get_option('RegionalPrompter')]
                    ]

            for index, tab in enumerate(tabs):
                if tab[1] and tab[2]:
                    inner_page = QWidget()
                    if index == 0:
                        inner_page.setLayout(make_prompt_tab(tmp))
                    if index == 1:
                        inner_page.setLayout(make_hires_other_tab(tmp))
                    if index == 2:
                        inner_page.setLayout(make_lora_addnet_tab(tmp))
                    if index == 3:
                        inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    if index == 4:
                        inner_page = (make_control_net_tab(tmp, 0))
                    if index == 5:
                        rp_pixmap_scale = self.config.get_option('RegionalPrompterPixmapSize')
                        inner_page.setLayout(make_regional_prompter_tab(tmp, rp_pixmap_scale))
                    inner_tab.addTab(inner_page, tab[0])

            error_list_parameter = self.config.get_option('ErrorList')
            if not error_list_parameter == 0:
                error_list = tmp.error_list
                difference = set(tmp.params.keys() - tmp.used_params.keys())
                if error_list or difference or error_list_parameter == 2:
                    diff_text = 'Diff: ' + ','.join(difference)
                    error_text = 'Error: ' + ','.join(error_list)
                    inner_page = QWidget()
                    inner_page_layout = QVBoxLayout()
                    original_data = tmp.original_data
                    error = QTextEdit()
                    error.setPlainText(diff_text + '\n\n' + error_text)
                    original = QTextEdit()
                    original.setPlainText(original_data)
                    description_text = 'If an error occurs, please share the developer data displayed here.'
                    description = QLabel(description_text)
                    inner_page_layout.addWidget(original)
                    inner_page_layout.addWidget(error)
                    inner_page_layout.addWidget(description)
                    inner_page.setLayout(inner_page_layout)
                    inner_tab.addTab(inner_page, 'Errors')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            self.root_tab.addTab(tab_page, tmp.params.get('Filename'))
            self.root_tab.currentChanged.connect(self.tab_changed)

            image_count = image_count + 1
            if 'File count' in tmp.params:
                del tmp.params['File count']

        self.tab_max_count = self.root_tab.count()
        root_layout.addWidget(self.root_tab)

        button_layout = QHBoxLayout()
        button_text = ['Copy positive', 'Copy negative', 'Copy seed']
        if self.config.get_option('JsonExport'):
            button_text.extend(['Export JSON (This)', 'Export JSON (All)'])
        button_text.append('Reselect')
        if self.config.get_option('ModelHashExtractor'):
            button_text.append('M')
        for tmp in button_text:
            copy_button = QPushButton(tmp)
            copy_button.setObjectName(tmp)
            if tmp == 'M':
                copy_button.setMaximumSize(25, 25)
            button_layout.addWidget(copy_button)
            copy_button.clicked.connect(self.button_clicked)

        root_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        if self.progress_bar_enable:
            self.progress_bar.close()

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
        where_from = self.sender().objectName()
        clipboard = QApplication.clipboard()
        if where_from == 'Copy positive':
            if self.positive_for_copy:
                clipboard.setText(self.positive_for_copy)
        elif where_from == 'Copy negative':
            if self.negative_for_copy:
                clipboard.setText(self.negative_for_copy)
        elif where_from == 'Copy seed':
            if self.seed_for_copy:
                clipboard.setText(self.seed_for_copy)
        elif where_from == 'Export JSON (This)':
            data = self.params[self.tab_index].params
            filename = self.config.get_option('JsonSingle')
            if filename == 'filename':
                filename = self.params[self.tab_index].params.get('Filepath')
                filename = os.path.splitext(os.path.basename(filename))[0] + '.json'
            filepath = savefile_choose_dialog(filename)
            if filepath:
                pyPromptChecker.lib.io.export_json(data, filepath)
        elif where_from == 'Export JSON (All)':
            filename = self.config.get_option('JsonMultiple')
            if filename == 'directory':
                filename = self.params[0].params.get('Filepath')
                filename = os.path.basename(os.path.dirname(filename)) + '.json'
            filepath = savefile_choose_dialog(filename)
            if filepath:
                dict_list = []
                for tmp in self.params:
                    dict_list.append(tmp.params)
                pyPromptChecker.lib.io.export_json(dict_list, filepath)
        elif where_from == 'Reselect':
            filepath = file_choose_dialog()[0]
            if filepath:
                self.params = []
                self.init_ui(filepath)
        elif where_from == 'M':
            text = 'This operation requires a significant amount of time.'
            text = text + '\n...And more than 32GiB of memory.'
            text = text + '\nDo you still want to run it ?'
            if show_messagebox('Confirm', text, 'cancel', 'ques', self):
                directory = directory_choose_dialog()
                if directory:
                    operation_progress = ProgressDialog(self)
                    pyPromptChecker.lib.io.model_hash_maker(directory, operation_progress)
                    show_messagebox('Finished', 'Finished!')

    def managing_button_clicked(self):
        where_from = self.sender().text()
        if where_from == 'Favourite':
            source = self.params[self.tab_index].params.get('Filepath')
            destination = self.config.get_option('Favourites')
            is_move = not self.config.get_option('UseCopyInsteadOfMove')
            if not os.path.exists(source):
                text = "Can't find this image file."
                show_messagebox("Can't move", text, 'crit')
            elif not destination:
                text = "Can't find setting of destination directory.\nCheck setting in 'config.ini' file."
                show_messagebox("Can't move", text, 'crit')
            elif not os.path.isdir(destination):
                text = "Can't find destination directory.\nCheck setting in 'config.ini' file."
                show_messagebox("Can't move", text, 'crit')
            else:
                pyPromptChecker.lib.io.image_copy_to(source, destination, is_move)
        elif where_from == 'Move to':
            source = self.params[self.tab_index].params.get('Filepath')
            destination = directory_choose_dialog()
            is_move = not self.config.get_option('UseCopyInsteadOfMove')
            if destination:
                pyPromptChecker.lib.io.image_copy_to(source, destination, is_move)
        elif where_from == 'Delete':
            source = self.params[self.tab_index].params.get('Filepath')
            trash_bin = os.path.join(os.path.abspath(''), '.trash')
            os.makedirs(trash_bin, exist_ok=True)
            pyPromptChecker.lib.io.image_copy_to(source, trash_bin, True)

    def pixmap_clicked(self):
        self.image_window.filepath = self.params[self.tab_index].params.get('Filepath')
        self.image_window.init_ui()

    def closeEvent(self, event):
        trash_bin = os.path.join(os.path.abspath(''), '.trash')
        if not pyPromptChecker.lib.io.is_directory_empty(trash_bin):
            res = True
            ask = self.config.get_option('AskIfClearTrashBin')
            if ask:
                res = show_messagebox('Clear trash bin', 'Do you want to clean up trash bin ?', 'ques')
            if res or not ask:
                pyPromptChecker.lib.io.clear_trash_bin(trash_bin)
        event.accept()
        QApplication.quit()


def move_center(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())


def result_window(target_data):
    app = QApplication(sys.argv)
    window = ResultWindow(target_data)
    window.show()
    sys.exit(app.exec())


def make_main_section(target, scale):
    status = [['File count', 'Number'],
              'Filename',
              'Filepath',
              'Timestamp',
              'Size',
              'Seed',
              'Sampler',
              'Eta',
              'Steps',
              'CFG scale',
              ['Dynamic thresholding enabled', 'CFG scale fix'],
              'Model',
              ['Variation seed', 'Var. seed'],
              ['Variation seed strength', 'Var. strength'],
              'Seed resize from',
              ['Denoising strength', 'Denoising'],
              'Clip skip',
              ['Lora', 'Lora in prompt'],
              ['AddNet Number', 'Add network'],
              ['Hires upscaler', 'Hires.fix'],
              'Tiled diffusion',
              'Region control',
              'ControlNet',
              'ENSD',
              'Version'
              ]
    filepath = target.params.get('Filepath')
    if target.params.get('Hires upscaler'):
        del status[15]
    timestamp = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
    target.params['Timestamp'] = timestamp.strftime('%Y/%m/%d %H:%M')
    main_section_layout = QHBoxLayout()
    pixmap_label = make_pixmap_label(filepath, scale)
    main_section_layout.addLayout(pixmap_label, 1)
    main_section_layout.insertSpacing(1, 10)
    main_section_layout.addLayout(label_maker(status, target, 1, 1, True, True, 15), 1)

    return main_section_layout


def make_pixmap_label(filepath, scale):
    pixmap_layout = QVBoxLayout()
    button_layout = QHBoxLayout()
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(scale, scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    pixmap_label = PixmapLabel()
    pixmap_label.setPixmap(pixmap)
    pixmap_label.setObjectName('Pixmap')
    pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap_layout.addWidget(pixmap_label)
    for tmp in ['Favourite', 'Move to', 'Delete']:
        button = QPushButton(tmp)
        button.setObjectName(tmp)
        button_layout.addWidget(button)
    pixmap_layout.addLayout(button_layout)
    return pixmap_layout


def make_prompt_tab(target):
    textbox_tab_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)
    positive_text = target.params.get('Positive')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    negative_text = target.params.get('Negative')
    negative_prompt = QTextEdit(negative_text)
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_tab_layout.addWidget(splitter)

    target.used_params['Positive'] = True
    target.used_params['Negative'] = True

    return textbox_tab_layout


def make_hires_other_tab(target):
    tab_layout = QHBoxLayout()
    hires_section = make_hires_section(target)
    tab_layout.addLayout(hires_section)
    cfg_fix_section = dynamic_thresholding_section(target)
    tab_layout.addWidget(cfg_fix_section)
    return tab_layout


def make_hires_section(target):
    hires_section_layout = QVBoxLayout()

    status = [['Hires upscaler', 'Upscaler'],
              ['Hires upscale', 'Upscale'],
              ['Hires resize', 'Resize'],
              ['Hires steps', 'Steps'],
              ['Denoising strength', 'Denoising']
              ]
    hires_group = QGroupBox()
    hires_group.setTitle('Hires.fix')
    if not target.params.get('Hires upscaler'):
        hires_group.setDisabled(True)
    else:
        if not target.params.get(status[3][0]):
            status[3][0] = 'Steps'
    hires_group.setLayout(label_maker(status, target, 4, 6))

    status = ['Face restoration']
    face_section = QGroupBox()
    face_section.setTitle('Face restoration')
    item = target.params.get('Face restoration')
    if not item:
        face_section.setDisabled(True)
    face_section.setLayout(label_maker(status, target, 2, 1, False))

    hires_section_layout.addWidget(hires_group, 2)
    hires_section_layout.addWidget(face_section, 1)
    return hires_section_layout


def dynamic_thresholding_section(target):
    status = ['CFG mode',
              'CFG scale minimum',
              'Mimic mode',
              'Mimic scale',
              'Mimic scale minimum',
              'Scheduler value',
              'Threshold percentile',
              ['Separate Feature Channels', 'Separate feature channels'],
              ['Scaling Startpoint', 'Scaling startpoint'],
              ['Variability Measure', 'Variability measure'],
              ['Interpolate Phi', 'Interpolate phi']
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 6, 4))
    section.setTitle('Dynamic thresholding (CFG scale fix)')
    if not target.params.get('Dynamic thresholding enabled'):
        section.setDisabled(True)
    return section


def make_lora_addnet_tab(target):
    tab_layout = QHBoxLayout()
    lora_group = make_lora_section(target)
    tab_layout.addWidget(lora_group, 3)
    addnet_group = make_addnet_section(target)
    tab_layout.addWidget(addnet_group, 4)
    return tab_layout


def make_lora_section(target):
    lora_section = QGroupBox()
    section_layout = QVBoxLayout()
    lora_num = target.params.get('Lora')
    if not lora_num:
        caption = 'Lora in prompt : 0'
    else:
        caption = 'Lora in prompt : ' + lora_num
        loop_num = max(int(lora_num), 14) + 1
        keyring = []
        for i in range(loop_num):
            key = 'Lora ' + str(i)
            title = 'Lora ' + str(i + 1)
            if target.params.get(key):
                keyring.append([key, title])
            else:
                keyring.append([None, None])
        section_layout.addLayout(label_maker(keyring, target, 1, 3))
    lora_section.setLayout(section_layout)
    lora_section.setTitle(caption)
    return lora_section


def make_addnet_section(target):
    status = [['Module', 'Module'],
              ['Weight A', 'UNet / TEnc'],
              ['Model', 'Model']
              ]
    addnet_section = QGroupBox()
    addnet = target.params.get('AddNet Enabled')
    section_layout = QVBoxLayout()
    if not addnet:
        addnet_section.setDisabled(True)
        cnt = 0
    else:
        cnt = 5
        for i in range(1, 6):
            key = [['AddNet ' + value[0] + ' ' + str(i), value[1]] for value in status]
            if not target.params.get(key[0][0]):
                key = [None, None, None]
                cnt = cnt - 1
            section_layout.addLayout(label_maker(key, target, 1, 3))
    addnet_section.setLayout(section_layout)
    addnet_section.setTitle('Additional Networks : ' + str(cnt))
    target.used_params['AddNet Enabled'] = True
    return addnet_section


def make_tiled_diffusion_tab(target):
    tab_layout = QHBoxLayout()
    tiled_diffusion_section = QVBoxLayout()
    tiled_diffusion_basic_info = make_tiled_diffusion_section(target)
    noise_inversion_info = make_noise_inversion_section(target)
    region_control_info = region_control_section(target)

    tiled_diffusion_section.addWidget(tiled_diffusion_basic_info)
    tiled_diffusion_section.addWidget(noise_inversion_info)

    tab_layout.addLayout(tiled_diffusion_section, 1)
    tab_layout.addWidget(region_control_info, 1)
    return tab_layout


def make_tiled_diffusion_section(target):
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
    section.setLayout(label_maker(status, target, 2, 3))
    return section


def make_noise_inversion_section(target):
    status = ['Noise inversion Kernel size',
              'Noise inversion Renoise strength',
              'Noise inversion Retouch',
              'Noise inversion Steps'
              ]
    section = QGroupBox()
    section.setTitle('Noise inversion')
    target.used_params['Noise inversion'] = True
    if not target.params.get('Noise inversion'):
        section.setDisabled(True)
    status = [[value, value.replace('Noise inversion ', '')] for value in status]
    section.setLayout(label_maker(status, target, 2, 3))
    return section


def region_control_section(target):
    status = [['blend mode', 'Blend mode'],
              ['feather ratio', 'Feather ratio'],
              ['w', 'Width'],
              ['h', 'Height'],
              ['x', 'X'],
              ['y', 'Y'],
              ['seed', 'Seed'],
              ]
    region_control_tab = QTabWidget()
    for i in range(1, 9):
        region_number = 'Region ' + str(i)
        check = target.params.get(region_number + ' enable')
        target.used_params[region_number + ' enable'] = True
        if check or i == 1:
            page = QWidget()
            region_control_section_layout = QVBoxLayout()
            keys = [[region_number + ' ' + value[0], value[1]] for value in status]
            region_control_section_layout.addLayout(label_maker(keys, target, 1, 1, True))
            str_prompt = target.params.get(region_number + ' prompt')
            prompt = QTextEdit(str_prompt)
            prompt.setReadOnly(True)
            region_control_section_layout.addWidget(prompt)
            target.used_params[region_number + ' prompt'] = True
            str_negative_prompt = target.params.get(region_number + ' neg prompt')
            negative_prompt = QTextEdit(str_negative_prompt)
            negative_prompt.setReadOnly(True)
            region_control_section_layout.addWidget(negative_prompt)
            target.used_params[region_number + ' neg prompt'] = True
            page.setLayout(region_control_section_layout)
            region_control_tab.addTab(page, region_number)
            if not check:
                region_control_tab.setDisabled(True)
    return region_control_tab


def make_control_net_tab(target, starts):
    control_tab = QScrollArea()
    controlnet_widget = QWidget()
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
    control_tab.setWidgetResizable(True)
    control_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    control_tab.setStyleSheet('QScrollArea {background-color:transparent;}')

    unit_num = int(target.params.get('ControlNet'))
    loop_num = 2 if 2 > unit_num else unit_num
    #    loop_num = 10
    for i in range(starts, loop_num):
        control_net_enable = target.params.get('ControlNet ' + str(i))
        status_key = [['ControlNet ' + str(i) + ' ' + value[0], value[1]] for value in status]
        section = QGroupBox()
        section.setTitle('ControlNet Unit ' + str(i))
        if not control_net_enable:
            section.setDisabled(True)
        else:
            target.used_params['ControlNet ' + str(i)] = True
        section.setLayout(label_maker(status_key, target, 4, 6))
        page_layout.addWidget(section)
    controlnet_widget.setLayout(page_layout)
    controlnet_widget.setStyleSheet('background-color:transparent')
    control_tab.setWidget(controlnet_widget)
    return control_tab


def make_regional_prompter_tab(target, scale):
    filepath = target.params.get('Filepath')
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(scale, int(scale * 0.7), Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.FastTransformation)

    regional_prompter_group = QHBoxLayout()
    regional_prompter_group.addWidget(make_regional_prompter_status_section(target), 1)

    ratio_pixmap_label = QLabel()
    str_ratios = target.params.get('RP Ratios')
    ratio_mode = target.params.get('RP Matrix submode')
    if not ratio_mode:
        ratio_mode = '---'
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
              ['RP Change AND', '"AND" to "BREAK"'],
              ['RP LoRA Neg U Ratios', 'Lora negative UNet ratio'],
              ['RP LoRA Neg Te Ratios', 'Lora negative TEnc ratio'],
              ['RP threshold', 'Threshold']]
    status_section = QGroupBox()
    status_section.setLayout(label_maker(status, target, 2, 1))
    status_section.setTitle('Status')
    target.used_params['RP Active'] = True
    target.used_params['RP Matrix submode'] = True
    target.used_params['RP Ratios'] = True
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
            if ';' in str_ratio:
                main_ratio.append(int(ratio[0]))
                sub_ratio.append([int(number) for number in ratio[1:]])
            elif divide_mode == 'Horizontal':
                main_ratio.append(1)
                sub_ratio.append([int(number) for number in ratio])
            else:
                pass
        except ValueError:
            result = False
            break

    if not result:
        return None, None
    else:
        return main_ratio, sub_ratio


# def make_other_tab(target):
#    page_layout = QHBoxLayout()
#    page_layout.addWidget()
#    for i in range(2):
#        page_layout.addWidget(make_dummy_section(7))
#    return page_layout


# def make_dummy_section(num):
#    section = QGroupBox()
#    section_layout = QVBoxLayout()
#    for i in range(num):
#        title = QLabel()
#        section_layout.addWidget(title)
#    section.setLayout(section_layout)
#    section.setTitle('Dummy')
#    section.setDisabled(True)
#    return section


def label_maker(status, target, stretch_title, stretch_value, selectable=False, remove_if_none=False, minimums=99):
    label_count = 0
    section_layout = QGridLayout()
    for tmp in status:
        if isinstance(tmp, list):
            item = target.params.get(tmp[0])
            key, name = tmp
        else:
            item = target.params.get(tmp)
            key = name = tmp
        if item:
            if 'Filepath' in key:
                item = os.path.dirname(item)
            elif 'ControlNet' in key and 'model' in key:
                item = item.replace(' ', '\n')
            elif 'Hires.fix' in name:
                item = 'True'
            elif 'AddNet' in key and 'Model' in key:
                item = item.replace('(', ' [').replace(')', ']')
            elif 'AddNet' in key and 'Weight A' in key:
                weight_b_key = key.replace(' A ', ' B ')
                weight_b = target.params.get(weight_b_key)
                item = item + ' / ' + weight_b
                target.used_params[weight_b_key] = True
        else:
            if name == 'Keep input size':
                item = 'False'
            elif name and not remove_if_none:
                item = 'None'
        if not item and remove_if_none:
            continue
        title = QLabel(name)
        value = QLabel(item)
        if selectable:
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if name:
            title.setObjectName(name + '_title')
            value.setObjectName(name + '_value')
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(stretch_title)
        size_policy_value.setHorizontalStretch(stretch_value)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        section_layout.addWidget(title, label_count, 0)
        section_layout.addWidget(value, label_count, 1)
        label_count = label_count + 1
        if not item == 'None':
            target.used_params[key] = True
    if 20 > minimums > label_count:
        for i in range(minimums - label_count):
            margin = QLabel()
            section_layout.addWidget(margin, label_count, 0)
            label_count = label_count + 1
    return section_layout


def savefile_choose_dialog(filename=None):
    caption = 'Save File'
    path = os.path.expanduser('~')
    default_filename = os.path.join(path, 'parameters.json')
    if filename:
        default_filename = os.path.join(path, filename)
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


def show_messagebox(title, text, method='', icon='', parent=None):
    messagebox = QMessageBox()
    messagebox.addButton(QMessageBox.StandardButton.Ok)
    if icon == 'crit':
        messagebox.setIcon(QMessageBox.Icon.Critical)
    elif icon == 'Warn':
        messagebox.setIcon(QMessageBox.Icon.Warning)
    elif icon == 'ques':
        messagebox.setIcon(QMessageBox.Icon.Question)
    else:
        messagebox.setIcon(QMessageBox.Icon.Information)
    if method == 'cancel':
        messagebox.addButton(QMessageBox.StandardButton.Cancel)
    messagebox.setText(text)
    if not messagebox.exec() == 1024:
        return False
    move_center(messagebox, parent)
    return True


def progress_dialog():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    progress = ProgressDialog()
    return app, progress
