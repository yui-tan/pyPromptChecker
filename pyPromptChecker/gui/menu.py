# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtGui import QAction


def quit_triggered():
    QApplication.quit()


class MainMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.main = parent

        self.reselect_menu = QMenu('Reselect', self)
        self.reselect_add = QAction('Add new tabs', self.reselect_menu)
        self.reselect_renewal = QAction('Renewal', self.reselect_menu)

        self.json_export_menu = QMenu('Export JSON', self)
        self.json_export_single = QAction("Present image", self.json_export_menu)
        self.json_export_all = QAction("All images", self.json_export_menu)
        self.json_export_selected = QAction('Image selection', self)

        self.json_import_menu = QMenu('Import JSON', self)
        self.json_import_files = QAction("Select files", self.json_import_menu)
        self.json_import_directory = QAction("Select directory", self.json_import_menu)

        self.model_hash_extractor = QAction('Model hash extractor', self)
        self.quit = QAction('Quit', self)

        self.addAction(self.model_hash_extractor)

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

        self.addAction(self.quit)

        self.quit.triggered.connect(quit_triggered)
        self.model_hash_extractor.triggered.connect(self.main.model_hash_extractor)
        self.reselect_add.triggered.connect(self.main.not_yet_implemented)
        self.reselect_renewal.triggered.connect(self.main.reselect_files)
        self.json_import_files.triggered.connect(self.main.not_yet_implemented)
        self.json_import_directory.triggered.connect(self.main.not_yet_implemented)
        self.json_export_single.triggered.connect(self.main.export_json_single)
        self.json_export_all.triggered.connect(self.main.export_json_all)
        self.json_export_selected.triggered.connect(self.main.export_json_selected)