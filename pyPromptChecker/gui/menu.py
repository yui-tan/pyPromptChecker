# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


class FileManageMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main = parent

        self.delete_menu = QMenu('Delete', self)
        self.delete = QAction('Confirm', self.delete_menu)
        self.delete.setObjectName('Delete')
        self.move_to = QAction('Move to', self)
        self.move_to.setObjectName('Move')
        self.add_favourite = QAction('Add favourite', self)
        self.add_favourite.setObjectName('Add favourite')

        self.__menu_position()
        self.__menu_trigger()

    def __menu_position(self):
        self.addMenu(self.delete_menu)
        self.delete_menu.addAction(self.delete)

        self.addSeparator()

        self.addAction(self.move_to)
        self.addAction(self.add_favourite)

    def __menu_trigger(self):
        self.delete.triggered.connect(lambda: self.main.signal_received())
        self.move_to.triggered.connect(lambda: self.main.signal_received())
        self.add_favourite.triggered.connect(lambda: self.main.signal_received())


class SearchMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main = parent

        self.restore = QAction('Restore', self)
        self.search = QAction('Search', self)
        self.search_selected = QAction('Search in selected files', self)
        self.init_search = QAction('Search initial image', self)

        self.__menu_position()

    def __menu_position(self):
        self.addAction(self.restore)

        self.addSeparator()

        self.addAction(self.init_search)
        self.addAction(self.search_selected)
        self.addAction(self.search)


class TabMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main = parent

        self.tab_link = QAction('Compare extension', self)
        self.addAction(self.tab_link)
        self.tab_link.setCheckable(True)

        self.tab_link.triggered.connect(self.main.toggle_tab_link)


class MainMenu(QMenu):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.main = controller
        self.window = parent

        self.lora_wizard = QAction('LoRa wizard', self)
        self.interrogate_menu = QMenu('Interrogate', self)
        self.interrogate_wd14 = QMenu('WD 1.4 Tagger', self)
        self.interrogate_all = QAction('All images', self)
        self.interrogate_selected = QAction('Selected images', self)
        self.interrogate_this = QAction('This image', self)

        self.reselect_menu = QMenu('Reselect', self)

        self.reselect_from_file = QMenu('Select files', self.reselect_menu)
        self.reselect_add_file = QAction('Append images', self.reselect_from_file)
        self.reselect_renewal_file = QAction('Replace all images', self.reselect_from_file)

        self.reselect_from_dir = QMenu('Select directory', self.reselect_menu)
        self.reselect_add_dir = QAction('Append tabs', self.reselect_from_dir)
        self.reselect_renewal_dir = QAction('Replace all images', self.reselect_from_dir)

        self.json_export_menu = QMenu('Export JSON', self)
        self.json_export_single = QAction("Present image", self.json_export_menu)
        self.json_export_all = QAction("All images", self.json_export_menu)
        self.json_export_selected = QAction('Selected images', self)

        self.json_import_menu = QMenu('Import JSON', self)
        self.json_import_files = QAction("Select files", self.json_import_menu)
        self.json_import_directory = QAction("Select directory", self.json_import_menu)

        self.model_hash_extractor = QAction('Model hash extractor', self)
        self.quit = QAction('Quit', self)
        self.dark_mode = QAction('Dark mode', self)
        self.dark_mode.setCheckable(True)

        self.__menu_position()
        self.__menu_trigger()

        self.theme_check()

    def __menu_position(self):

        self.addAction(self.model_hash_extractor)

        self.addSeparator()

        self.addAction(self.lora_wizard)
        self.interrogate_wd14.addActions([self.interrogate_all, self.interrogate_selected, self.interrogate_this])
        self.interrogate_menu.addMenu(self.interrogate_wd14)
        self.addMenu(self.interrogate_menu)
        self.lora_wizard.setDisabled(True)

        self.addSeparator()

        self.reselect_from_dir.addActions([self.reselect_add_dir, self.reselect_renewal_dir])
        self.reselect_menu.addMenu(self.reselect_from_dir)
        self.reselect_from_file.addActions([self.reselect_add_file, self.reselect_renewal_file])
        self.reselect_menu.addMenu(self.reselect_from_file)
        self.addMenu(self.reselect_menu)

        self.addSeparator()

        self.json_import_menu.addAction(self.json_import_files)
        self.json_import_menu.addAction(self.json_import_directory)
        self.addMenu(self.json_import_menu)

        self.json_export_menu.addAction(self.json_export_single)
        self.json_export_menu.addAction(self.json_export_all)
        self.json_export_menu.addAction(self.json_export_selected)
        self.addMenu(self.json_export_menu)

        self.addSeparator()

        self.addAction(self.dark_mode)

        self.addSeparator()

        self.addAction(self.quit)

    def __menu_trigger(self):
        self.quit.triggered.connect(self.__exit_app)
        self.dark_mode.triggered.connect(lambda: self.main.request_reception('theme', sender=self.window))
        self.model_hash_extractor.triggered.connect(lambda: self.main.request_reception('hash', sender=self.window))
        self.reselect_add_file.triggered.connect(lambda: self.__reselect_files('files', 'append'))
        self.reselect_renewal_file.triggered.connect(lambda: self.__reselect_files('files', 'replace'))
        self.reselect_add_dir.triggered.connect(lambda: self.__reselect_files('directory', 'append'))
        self.reselect_renewal_dir.triggered.connect(lambda: self.__reselect_files('directory', 'replace'))
        self.json_import_files.triggered.connect(lambda: self.__json_import('files', True))
        self.json_import_directory.triggered.connect(lambda: self.__json_import('directory', True))
        self.json_export_single.triggered.connect(lambda: self.__json_export('single'))
        self.json_export_all.triggered.connect(lambda: self.__json_export('all'))
        self.json_export_selected.triggered.connect(lambda: self.__json_export('select'))
        self.interrogate_this.triggered.connect(self.__interrogate_request)
        self.interrogate_all.triggered.connect(lambda: self.__interrogate_request('all'))
        self.interrogate_selected.triggered.connect(lambda: self.__interrogate_request('selected'))

    def __exit_app(self):
        self.main.request_reception('exit', self.window)

    def __reselect_files(self, which: str, replace_or_append: str):
        self.main.request_reception(replace_or_append, self.window, condition=which)

    def __json_import(self, which: str, is_replace: bool):
        self.main.request_reception('import', self.window, indexes=(which, is_replace))

    def __json_export(self, which: str):
        if hasattr(self.window, 'get_selected_images'):
            result = None
            if which == 'select':
                result = self.window.get_selected_images(True)
            elif which == 'all':
                result = self.window.get_selected_images(False)
            elif which == 'single':
                if hasattr(self.window, 'root_tab'):
                    result = (self.window.root_tab.currentIndex(),)
            if result:
                self.main.request_reception('json', self.window, indexes=result)

    def __interrogate_request(self, which: str):
        if hasattr(self.window, 'interrogate_emit'):
            if which == 'select':
                self.window.interrogate_emit('selected')
            elif which == 'all':
                self.window.interrogate_emit('entire')
            else:
                self.window.interrogate_emit()
        elif hasattr(self.window, 'get_selected_images'):
            indexes = None
            if which == 'selected':
                indexes = self.window.get_selected_images()
            elif which == 'all':
                indexes = self.window.get_selected_images(False)
            if indexes:
                self.main.request_reception('interrogate', self.window, indexes=indexes)

    def present_check(self, destination):
        if not hasattr(destination, 'root_tab'):
            self.json_export_single.setDisabled(True)
            self.interrogate_this.setDisabled(True)
        else:
            self.json_export_single.setDisabled(False)
            self.interrogate_this.setDisabled(False)

    def theme_check(self):
        if self.main.dark:
            self.dark_mode.setChecked(True)
        else:
            self.dark_mode.setChecked(False)
