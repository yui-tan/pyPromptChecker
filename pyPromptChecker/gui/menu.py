# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtGui import QAction


def quit_triggered():
    QApplication.quit()


class MainMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main = parent

        self.lora_wizard = QAction('LoRa wizard', self)
        self.interrogate_menu = QMenu('Interrogate', self)
        self.interrogate_wd14 = QMenu('WD 1.4 Tagger', self)
        self.interrogate_defaults = QMenu('Default threshold', self)
        self.interrogate_specify = QMenu('Specify threshold', self)
        self.interrogate_all = QAction('All images', self)
        self.interrogate_selected = QAction('Select images', self)
        self.interrogate_this = QAction('This image', self)

        self.reselect_menu = QMenu('Reselect', self)
        self.reselect_add = QAction('Append tabs', self.reselect_menu)
        self.reselect_renewal = QAction('Repalece all tabs', self.reselect_menu)

        self.json_export_menu = QMenu('Export JSON', self)
        self.json_export_single = QAction("Present image", self.json_export_menu)
        self.json_export_all = QAction("All images", self.json_export_menu)
        self.json_export_selected = QAction('Image selection', self)

        self.json_import_menu = QMenu('Import JSON', self)
        self.json_import_files = QAction("Select files", self.json_import_menu)
        self.json_import_directory = QAction("Select directory", self.json_import_menu)

        self.model_hash_extractor = QAction('Model hash extractor', self)
        self.quit = QAction('Quit', self)
        self.dark_mode = QAction('Dark mode', self)
        self.dark_mode.setCheckable(True)

        self.theme_check()

        self.addAction(self.model_hash_extractor)

        self.addSeparator()

        self.addAction(self.lora_wizard)
        self.interrogate_defaults.addActions([self.interrogate_all, self.interrogate_selected, self.interrogate_this])
        self.interrogate_specify.addActions([self.interrogate_all, self.interrogate_selected, self.interrogate_this])
        self.interrogate_wd14.addMenu(self.interrogate_defaults)
        self.interrogate_wd14.addMenu(self.interrogate_specify)
        self.interrogate_menu.addMenu(self.interrogate_wd14)
        self.addMenu(self.interrogate_menu)
        self.lora_wizard.setDisabled(True)
        self.interrogate_menu.setDisabled(True)

        self.addSeparator()

        self.reselect_menu.addAction(self.reselect_add)
        self.reselect_menu.addAction(self.reselect_renewal)
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

        self.quit.triggered.connect(quit_triggered)
        self.dark_mode.triggered.connect(self.main.change_themes)
        self.model_hash_extractor.triggered.connect(self.main.model_hash_extractor)
        self.reselect_add.triggered.connect(self.main.reselect_files_append)
        self.reselect_renewal.triggered.connect(self.main.reselect_files)
        self.json_import_files.triggered.connect(self.main.import_json_from_files)
        self.json_import_directory.triggered.connect(self.main.import_json_from_directory)
        self.json_export_single.triggered.connect(self.main.export_json_single)
        self.json_export_all.triggered.connect(self.main.export_json_all)
        self.json_export_selected.triggered.connect(self.main.open_thumbnail)

    def theme_check(self):
        if self.main.dark:
            self.dark_mode.setChecked(True)
        else:
            self.dark_mode.setChecked(False)


class TabMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main = parent

        self.tab_link = QAction('Compare extension', self)
        self.addAction(self.tab_link)
        self.tab_link.setCheckable(True)

        self.tab_link.triggered.connect(self.main.tab_link)


class ThumbnailMenu(QMenu):
    pass


class ListviewMenu(QMenu):
    pass
