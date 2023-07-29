import csv
import os
import sys

from PyQt6.QtWidgets import QApplication

import libs.window
from libs.decoder import decode_text_chunk
from libs.parser import parse_parameter


def model_hashes():
    directory = os.path.dirname(__file__)
    filename = os.path.join(directory, 'model_list.csv')
    with open(filename, encoding='utf8', newline='') as f:
        csvreader = csv.reader(f)
        model_list = [row for row in csvreader]
    return model_list


def main():
    app = QApplication(sys.argv)
    src = libs.window.file_choose_dialog()
    models = model_hashes()
    if src[0]:
        parameters_list = []
        for filepath in src[0]:
            chunk_data = decode_text_chunk(filepath, 1)
            parameters = parse_parameter(chunk_data, filepath, models)
            parameters_list.append(parameters)
        window = libs.window.ResultWindow(parameters_list)
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()
