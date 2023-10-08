# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QLineEdit
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QPalette

from .dialog import *
from .menu import *
from .widget import *
from . import config

HIDE_TAB = config.get('OpenWithShortenedWindow', False)
TAB_NAVIGATION_ENABLE = config.get('TabNavigation', True)
TAB_MINIMUMS = config.get('TabNavigationMinimumTabs', True)
THUMBNAIL_TAB_BAR = config.get('ThumbnailTabBar', False)
TAB_BAR_ORIENTATION = config.get('ThumbnailTabBarVertical', True)
ERROR_LIST_PARAMETER = config.get('ErrorList', 1)
USE_NUMBER = config.get('UsesNumberAsTabName', False)
HIDE_NORMAL_TAB_BAR = config.get('HideNormalTabBar', False)


class Tabview(QMainWindow):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.toast = None
        self.controller = controller
        self.setWindowTitle('PNG Prompt Data')
        self.setObjectName('Tabview')

        self.tab_pages = []
        self.root_tab = None
        self.tab_navigation = None
        self.tab_bar = None

        self.hide_tab = HIDE_TAB

        self.tab_link = False
        self.tab_link_menu = TabMenu(self)
        self.tab_link_index = 'Prompt'

    def init_tabview(self, loaded_images, moved=None, deleted=None):
        self.root_tab = None
        self.tab_pages = []

        central_widget = QWidget()
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(5, 5, 5, 5)

        footer_layout = make_footer_area(self)

        filelist = [value.params.get('Filename') for _, value in loaded_images]
        self.tab_navigation = TabNavigation(self, self.controller, filelist)
        root_layout.addWidget(self.tab_navigation)

        filepaths = [value.params.get('Filepath') for _, value in loaded_images]
        self.tab_bar = TabBar(filepaths, self.controller, self, TAB_BAR_ORIENTATION)
        middle_section = QWidget()

        self.root_tab = QTabWidget()
        self.root_tab.setObjectName('root_tab')

        if TAB_BAR_ORIENTATION:
            middle_section_layout = QHBoxLayout()
            middle_section_layout.addWidget(self.root_tab)
            middle_section_layout.addWidget(self.tab_bar)
        else:
            middle_section_layout = QVBoxLayout()
            middle_section_layout.addWidget(self.tab_bar)
            middle_section_layout.addWidget(self.root_tab)

        middle_section_layout.setContentsMargins(0, 0, 0, 0)
        middle_section.setLayout(middle_section_layout)
        root_layout.addWidget(middle_section)

        root_layout.addLayout(footer_layout)
        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        self.init_root_tab(loaded_images, moved, deleted)
        self.toast = Toast(self)

        self.show()
        move_centre(self)

    def init_root_tab(self, loaded_images, moved=None, deleted=None):
        shown_tab = self.root_tab.count()
        total = shown_tab + len(loaded_images)
        image_count = 0

        progress = ProgressDialog()
        progress.setLabelText('Formatting...')
        progress.setRange(0, len(loaded_images))

        for index, image in loaded_images:
            if total > 1:
                image.params['File count'] = str(shown_tab + image_count + 1) + ' / ' + str(total)

            tab_page = QWidget()
            tab_page.setObjectName(f'index_{index}')
            tab_page_layout = QVBoxLayout()
            tab_page_layout.setContentsMargins(5, 5, 5, 5)

            main_section = QGroupBox()
            main_section.setObjectName('main_section')
            main_section.setTitle(image.params.get('Filename', 'None'))
            image.used_params['Filename'] = True

            main_section_layout = QHBoxLayout()
            main_section_layout.setContentsMargins(5, 5, 0, 5)
            main_label_layout = make_main_section(image, self)
            main_section_layout.addLayout(main_label_layout)
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)

            main_section_height = config.get('PixmapSize', 350) + 60
            main_section.setFixedHeight(main_section_height)

            dummy_widget = QWidget()
            dummy_widget.setObjectName('dummy')
            tab_page_layout.addWidget(dummy_widget)

            hires_tab = ['Hires upscaler', 'Face restoration', 'Extras']
            cfg_fix_auto_tab = ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler']
            lora_tab = ['Lora', 'AddNet Enabled', 'Textual inversion']

            tabs = [['Prompts', True, True],
                    ['Hires.fix / Extras',
                     any(key in v for v in image.params for key in hires_tab),
                     config.get('HiresExtras', True)],
                    ['CFG',
                     any(key in v for v in image.params for key in cfg_fix_auto_tab),
                     config.get('CFG', True)],
                    ['LoRa / Add networks',
                     any(key in v for v in image.params for key in lora_tab),
                     config.get('LoraAddNet', True)],
                    ['Tiled diffusion',
                     'Tiled diffusion' in image.params,
                     config.get('TiledDiffusion', True)],
                    ['Control net',
                     'ControlNet' in image.params,
                     config.get('ControlNet', True)],
                    ['Regional prompter',
                     'RP Active' in image.params,
                     config.get('RegionalPrompter', True)]
                    ]

            inner_tab = QTabWidget()

            for i, tab in enumerate(tabs):
                if tab[1] and tab[2]:
                    inner_page = QWidget()
                    inner_page.setMinimumHeight(config.get('PixmapSize', 350))
                    if i == 0:
                        inner_page.setLayout(make_prompt_tab(image))
                    if i == 1:
                        inner_page.setLayout(make_hires_other_tab(image))
                    if i == 2:
                        inner_page.setLayout(make_cfg_tab(image))
                    if i == 3:
                        inner_page.setLayout(make_lora_addnet_tab(image))
                    if i == 4:
                        inner_page.setLayout(make_tiled_diffusion_tab(image))
                    if i == 5:
                        inner_page = make_control_net_tab(image, 0)
                    if i == 6:
                        inner_page = make_regional_prompter_tab(image)
                    inner_tab.addTab(inner_page, tab[0])

            if not ERROR_LIST_PARAMETER == 0:
                error_page = make_error_tab(image, ERROR_LIST_PARAMETER)
                inner_tab.addTab(error_page, 'Errors')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            inner_tab.setObjectName('extension_tab')
            inner_tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            inner_tab.customContextMenuRequested.connect(self.__show_tab_menu)
            inner_tab.currentChanged.connect(self.__tab_changed)

            if self.hide_tab:
                inner_tab.hide()

            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            if 'File count' in image.params:
                del image.params['File count']

            if USE_NUMBER:
                self.root_tab.addTab(tab_page, str(shown_tab + image_count))
            else:
                self.root_tab.addTab(tab_page, image.params.get('Filename', '---'))

            self.root_tab.setTabToolTip(shown_tab + image_count, image.params.get('Filename', '---'))
            self.root_tab.currentChanged.connect(self.__tab_changed)
            image_count += 1

            if progress:
                progress.update_value()

        total = self.root_tab.count()
        if all([THUMBNAIL_TAB_BAR, HIDE_NORMAL_TAB_BAR]) or total == 1:
            self.root_tab.tabBar().hide()
        if not all([TAB_NAVIGATION_ENABLE, TAB_MINIMUMS < total]):
            self.tab_navigation.hide()
        if not all([THUMBNAIL_TAB_BAR, TAB_MINIMUMS < total]):
            self.tab_bar.hide()

        if moved:
            for i in list(moved):
                self.manage_subordinates(i, 'moved')
        if deleted:
            for i in list(deleted):
                self.manage_subordinates(i, 'deleted')

        self.tab_navigation.toggle_button_availability(True)

        if progress:
            progress.close()

    def tabview_add_images(self, loaded_images):
        total = self.root_tab.count()
        if total < 2:
            self.init_tabview(loaded_images)
            return
        else:
            self.init_root_tab(loaded_images)

        total += len(loaded_images)
        for index in range(total):
            text = str(index + 1) + ' / ' + str(total)
            widget = self.root_tab.widget(index)
            label = widget.findChild(QLabel, 'Number_value')
            if label:
                label.setText(text)

            filelist = [value.params.get('Filename') for _, value in loaded_images]
            self.tab_navigation.refresh_combobox(filelist)

        if self.tab_bar:
            filelist = [value.params.get('Filepath') for _, value in loaded_images]
            self.tab_bar.add_tab(filelist)

    def toggle_tab_link(self):
        if self.tab_link:
            self.tab_link = False
        else:
            current_tab_index = self.root_tab.currentIndex()
            current_tab_page = self.root_tab.widget(current_tab_index)
            extension_tab = current_tab_page.findChild(QTabWidget, 'extension_tab')
            extension_tab_index = extension_tab.currentIndex()
            extension_tab_text = extension_tab.tabText(extension_tab_index) if extension_tab else None
            self.tab_link = True
            self.tab_link_index = extension_tab_text

    def tab_signal_received(self):
        where_from = self.sender().objectName()
        clipboard = QApplication.clipboard()
        current_page = self.root_tab.currentWidget()
        current_index = self.root_tab.currentIndex()

        if where_from == 'Copy positive':
            text_edit = current_page.findChild(QTextEdit, 'Positive')
            if text_edit:
                text = text_edit.toPlainText()
                if text and not text == 'This file has no embedded data':
                    clipboard.setText(text)
                    self.toast.init_toast('Positive Copied!', 1000)

        elif where_from == 'Copy negative':
            text_edit = current_page.findChild(QTextEdit, 'Negative')
            if text_edit:
                text = text_edit.toPlainText()
                if text:
                    clipboard.setText(text)
                    self.toast.init_toast('Negative Copied!', 1000)

        elif where_from == 'Copy seed':
            label = current_page.findChild(QLabel, 'Seed_value')
            if label:
                text = label.text()
                clipboard.setText(text)
                self.toast.init_toast('Seed Copied!', 1000)

        elif where_from == 'Shrink':
            # noinspection PyTypeChecker
            self.__change_window(self.sender())

        elif where_from == '▲Menu':
            x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
            y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.controller.main_menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.controller.main_menu.present_check(self)
            self.controller.main_menu.exec(adjusted_pos)

        elif where_from == 'bar_toggle':
            self.tab_bar.toggle_tab_bar(self.sender())
            button = self.centralWidget().findChild(QPushButton, 'bar_toggle')
            self.tab_bar.toggle_tab_bar(button)

        elif where_from == 'pixmap':
            self.controller.request_reception((current_index,), 'view', self)

        elif where_from == 'Favourite':
            result = self.controller.request_reception((current_index,), 'add')
            if result:
                self.toast.init_toast('Added!', 1000)

        elif where_from == 'Move to':
            result = self.controller.request_reception((current_index,), 'move')
            if result:
                self.toast.init_toast('Moved!', 1000)

        elif where_from == 'Delete':
            result = self.controller.request_reception((current_index,), 'delete')
            if result:
                self.toast.init_toast('Deleted!', 1000)

    def search_process(self, indexes: tuple = None):
        hide = config.get('HideNotMatchedTabs', False)
        if indexes:
            for tab_index in reversed(range(self.root_tab.count())):
                if tab_index not in indexes:
                    if hide:
                        title = self.root_tab.tabText(tab_index)
                        self.tab_pages.append([tab_index, self.root_tab.widget(tab_index), title])
                        self.root_tab.removeTab(tab_index)
                        self.tab_navigation.toggle_button_availability(False)
                else:
                    self.root_tab.tabBar().setTabTextColor(tab_index, Qt.GlobalColor.green)
                    self.tab_bar.image_matched(indexes)
                    if hide:
                        self.tab_bar.pixmap_hide()

        else:
            palette = self.root_tab.palette()
            text_color = palette.color(QPalette.ColorRole.Text)
            for index in range(self.root_tab.count()):
                color = self.root_tab.tabBar().tabTextColor(index)
                if color == Qt.GlobalColor.green:
                    self.root_tab.tabBar().setTabTextColor(index, text_color)
            if self.tab_pages:
                for widget in reversed(self.tab_pages):
                    self.root_tab.insertTab(widget[0], widget[1], widget[2])
                self.tab_pages = []
                self.tab_navigation.toggle_button_availability(True)
            if self.tab_bar:
                self.tab_bar.result_clear()

    def manage_subordinates(self, index: int, detail: str, remarks=None):
        for tab_index in range(self.root_tab.count()):
            tab_page = self.root_tab.widget(tab_index)
            main_section = tab_page.findChild(QWidget, 'main_section')
            move_delete_section = tab_page.findChild(QWidget, 'move_delete')
            filepath_label = main_section.findChild(QLabel, 'Filepath_value')
            tab_name = tab_page.objectName()
            number = int(tab_name.split('_')[1])
            if remarks:
                filename = os.path.basename(remarks)
                main_section.setTitle(filename)
                filepath_label.setText(remarks)
                filepath_label.setToolTip(remarks)
            if number == index:
                if detail == 'moved':
                    stylesheet = custom_stylesheet('colour', 'moved')
                    filepath_label.setStyleSheet(stylesheet)
                    self.root_tab.tabBar().setTabTextColor(tab_index, custom_color('Q_moved'))
                    if remarks:
                        move_delete_section.refresh_filepath(remarks)
                        self.root_tab.tabBar().setTabText(tab_index, filename)
                    if self.tab_bar:
                        self.tab_bar.image_moved((tab_index,))
                    break
                if detail == 'deleted':
                    stylesheet = custom_stylesheet('colour', 'deleted')
                    filepath_label.setStyleSheet(stylesheet)
                    self.root_tab.tabBar().setTabTextColor(tab_index, custom_color('Q_deleted'))
                    if remarks:
                        move_delete_section.refresh_filepath(remarks)
                        self.root_tab.tabBar().setTabText(tab_index, filename)
                    if self.tab_bar:
                        self.tab_bar.image_deleted((tab_index,))
                    break

    def __change_window(self, button):
        text = ''
        for index in range(self.root_tab.count()):
            extension_tab = self.root_tab.widget(index).findChild(QTabWidget, 'extension_tab')
            if extension_tab.isHidden():
                extension_tab.show()
                self.hide_tab = False
                text = 'Shrink'
            else:
                extension_tab.hide()
                self.hide_tab = True
                text = 'Expand'

        timer = QTimer(self)
        timer.timeout.connect(lambda: self.adjustSize())
        timer.start(10)

        button.setText(text)
        button.setShortcut(QKeySequence('Ctrl+Tab'))

    def __tab_changed(self):
        which_tab = self.sender().objectName()
        if which_tab == 'root_tab':
            current_index = self.root_tab.currentIndex()
            current_page = self.root_tab.widget(current_index)
            image_index = int(current_page.objectName().split('_')[1])
            extension_tab = current_page.findChild(QTabWidget, 'extension_tab')

            self.tab_navigation.current_changes(current_index)
            self.tab_bar.image_current(current_index)
            self.controller.request_reception((image_index,), 'change', self)

            if self.tab_link:
                tab_name = self.tab_link_index
                for index in range(extension_tab.count()):
                    if extension_tab.tabText(index) == tab_name:
                        extension_tab.setCurrentIndex(index)
                        break

        elif which_tab == 'extension_tab':
            current_index = self.sender().currentIndex()
            tab_name = self.sender().tabText(current_index)
            self.tab_link_index = tab_name

    def __show_tab_menu(self, pos):
        current_index = self.sender().currentIndex()
        tab_bar = self.sender().tabBar()
        tab_rect = tab_bar.tabRect(current_index)
        changed_pos = tab_bar.mapFrom(self.sender(), pos)
        if tab_rect.contains(changed_pos):
            x = tab_bar.mapToGlobal(tab_rect.topLeft()).x()
            y = tab_bar.mapToGlobal(tab_rect.topLeft()).y() - self.tab_link_menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.tab_link_menu.exec(adjusted_pos)


class TabNavigation(QWidget):
    def __init__(self, parent, controller, filelist):
        super().__init__(parent)
        self.tab = parent
        self.controller = controller
        self.dropdown = None
        self.filelist = filelist
        self.current = 0
        self.tab = parent
        self.__init_navigation()

    def __init_navigation(self):
        layout = QHBoxLayout()

        for text in ('Search', 'Restore', 'Listview', 'Thumbnail'):
            button = ButtonWithMenu(text)
            button.setObjectName(text)
            button.clicked.connect(self.__navi_signal_received)
            layout.addWidget(button, 1)

        self.dropdown = QComboBox()
        self.dropdown.addItems(self.filelist)
        self.dropdown.setEditable(True)
        self.dropdown.setObjectName('Dropdown')
        self.dropdown.currentIndexChanged.connect(self.__navi_signal_received)
        layout.insertWidget(2, self.dropdown, 5)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)
        self.setObjectName('TabNavigation')
        self.setStyleSheet('QWidget#TabNavigation { margin: 0; padding: 0; }')

    def __navi_signal_received(self):
        where_from = self.sender().objectName()
        if where_from == 'Search':
            self.controller.request_reception(None, 'search', self.tab)
        elif where_from == 'Restore':
            self.tab.search_process(None)
        elif where_from == 'Listview':
            self.controller.request_reception(None, 'list', self.tab)
        elif where_from == 'Thumbnail':
            self.controller.request_reception(None, 'thumbnail', self.tab)
        elif where_from == 'Dropdown':
            index = self.sender().currentIndex()
            self.tab.root_tab.setCurrentIndex(index)

    def refresh_combobox(self, filelist: list):
        self.filelist = filelist
        self.dropdown.clear()
        self.dropdown.addItems(filelist)

    def toggle_button_availability(self, is_disable):
        button = self.findChild(ButtonWithMenu, 'Restore')
        button.setDisabled(is_disable)

    def current_changes(self, index: int):
        self.dropdown.setCurrentIndex(index)


class TabBar(QWidget):
    def __init__(self, filepaths: list, controller, parent, vertical=False):
        super().__init__(parent)
        self.tab = parent
        self.controller = controller
        self.scroll_contents = QWidget()
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
        scroll.setStyleSheet('margin: 0px; border: none; padding: 0px')

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

        self.__tab_bar_thumbnails(self.filepaths)

    # noinspection PyUnresolvedReferences
    def __button_area(self):
        button_area_layout = QHBoxLayout()
        button_area_layout.setContentsMargins(0, 0, 0, 0)
        for text in (('S', 'Search'), ('R', 'Restore'), ('D', 'Diffview'), ('L', 'Listview'), ('T', 'Thumbnails')):
            button = QPushButton(text[0])
            button.setObjectName(text[0])
            button.setToolTip(text[1])
            button.setFixedSize(25, 25)
            button.clicked.connect(self.__button_clicked)
            button_area_layout.addWidget(button)
        return button_area_layout

    def __tab_bar_thumbnails(self, filepaths: list, starts=0):
        layout = self.scroll_contents.layout()
        for index, filepath in enumerate(filepaths):
            number = starts + index
            filename = os.path.basename(filepath)

            pixmap_label = PixmapLabel()
            pixmap_label.setObjectName('index_' + str(number))
            pixmap_label.setToolTip(filename)
            pixmap_label.clicked.connect(self.__pixmap_clicked)
            pixmap_label.rightClicked.connect(self.__pixmap_right_clicked)
            pixmap_label.ctrl_clicked.connect(self.__pixmap_ctrl_clicked)
            pixmap_label.shift_clicked.connect(self.__pixmap_shift_clicked)
            pixmap = portrait_generator(filepath, 100)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setFixedSize(100, 100)
            pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            pixmap_label.setStyleSheet('border: 1px solid palette(midlight)')

            layout.addWidget(pixmap_label)

    def __border_change(self, indexes: tuple, stylesheet: str):
        for index in indexes:
            target = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(index))
            target.setStyleSheet(stylesheet)

    def __border_clear(self, index: int):
        if self.moved and index in self.moved:
            self.image_moved((index,))
        elif self.deleted and index in self.deleted:
            self.image_deleted((index,))
        elif self.matched and index in self.matched:
            self.image_matched((index,))
        else:
            self.image_default(index)
        if self.selected:
            self.selected.discard(index)

    def __pixmap_clicked(self, right: bool = False, ctrl: bool = False, shift: bool = False):
        tmp = self.sender().objectName()
        number = int(tmp.split('_')[1])

        if right:
            self.controller.request_reception((number,), 'view', self.parent)

        elif ctrl:
            if number in self.selected:
                if len(self.selected) > 1:
                    self.__border_clear(number)
                else:
                    self.image_current(number)
            else:
                self.image_selected(number)

        elif shift:
            if self.current != number:
                starts = min(self.current, number)
                ends = max(self.current, number)
                for i in range(starts, ends + 1):
                    label = self.scroll_contents.findChild(PixmapLabel, 'index_' + str(i))
                    label.setStyleSheet(custom_stylesheet('border', 'current'))
                    if i not in self.selected:
                        self.selected.add(i)

        else:
            target = list(self.selected)
            for num in target:
                if num != number:
                    self.__border_clear(num)
                if number != self.current:
                    self.image_current(number)
                    self.tab.root_tab.setCurrentIndex(number)

    def __pixmap_right_clicked(self):
        self.__pixmap_clicked(right=True)

    def __pixmap_ctrl_clicked(self):
        self.__pixmap_clicked(ctrl=True)

    def __pixmap_shift_clicked(self):
        self.__pixmap_clicked(shift=True)

    def __button_clicked(self):
        where_from = self.sender().objectName()
        if where_from == 'S':
            self.controller.request_reception(tuple(self.selected), 'search', self.tab)
        elif where_from == 'R':
            pass
        elif where_from == 'D':
            self.controller.request_reception(tuple(self.selected), 'diff', self.tab)
        elif where_from == 'L':
            self.controller.request_reception(tuple(self.selected), 'list', self.tab)
        elif where_from == 'T':
            self.controller.request_reception(tuple(self.selected), 'thumbnail', self.tab)

    def add_tab(self, filepaths: list):
        add_items = [value for value in filepaths if value not in self.filepaths]
        self.__tab_bar_thumbnails(add_items, len(self.filepaths))
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

    def image_selected(self, index: int):
        self.__border_change((index, ), custom_stylesheet('border', 'current'))
        self.selected.add(index)

    def image_moved(self, indexes: tuple):
        stylesheet = 'border: 2px solid rgba(0, 0, 255, 0.5)'
        self.__border_change(indexes, stylesheet)
        self.moved.update(indexes)

    def image_deleted(self, indexes: tuple):
        stylesheet = 'border: 2px solid rgba(255, 0, 0, 0.5)'
        self.__border_change(indexes, stylesheet)
        self.deleted.update(indexes)

    def image_matched(self, indexes: tuple):
        stylesheet = 'border: 2px solid rgba(0, 255, 0, 0.5)'
        self.__border_change(indexes, stylesheet)
        self.matched.update(indexes)

    def image_current(self, index: int):
        self.__border_clear(self.current)
        self.__border_change((index,), custom_stylesheet('border', 'current'))
        self.current = index
        self.selected.add(index)

    def image_default(self, index: int):
        stylesheet = 'border: 1px solid palette(midlight)'
        self.__border_change((index,), stylesheet)

    def result_clear(self):
        self.matched.clear()
        widgets = self.scroll_contents.findChildren(PixmapLabel)
        for widget in widgets:
            if widget.isHidden:
                widget.show()
            tmp = widget.objectName()
            index = int(tmp.split('_')[1])
            self.__border_clear(index)
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
