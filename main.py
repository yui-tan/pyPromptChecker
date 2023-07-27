import csv
from libs.decoder import decode_text_chunk
from libs.parser import parse_parameter
from libs.window import show_result_window, file_choose_dialog


def model_hashes():
    with open('model_list.csv', encoding='utf8', newline='') as f:
        csvreader = csv.reader(f)
        model_list = [row for row in csvreader]
    return model_list


if __name__ == '__main__':
    src = file_choose_dialog()
    models = model_hashes()
    if src[0]:
        parameters_list = []
        for filepath in src[0]:
            chunk_data = decode_text_chunk(filepath, 1)
            parameters = parse_parameter(chunk_data, filepath, models)
            parameters_list.append(parameters)
        show_result_window(parameters_list)
