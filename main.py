import os
import sys
import argparse
import libs.window
import libs.decoder


def check_files(target_list):
    file_is_not_found_list = []
    this_is_directory_list = []
    this_file_is_not_png_file_list = []
    valid_file_list = []

    for filepath in target_list:
        if not os.path.exists(filepath):
            file_is_not_found_list.append(filepath)
        elif not os.path.isfile(filepath):
            this_is_directory_list.append(filepath)
        elif not libs.decoder.png_checker(filepath):
            this_file_is_not_png_file_list.append(filepath)
        else:
            valid_file_list.append(filepath)

    return valid_file_list, file_is_not_found_list, this_is_directory_list, this_file_is_not_png_file_list


if __name__ == '__main__':
    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog. --not yet implemented')
    group.add_argument('-f', '--filepath', nargs='*', type=str, help='Send path to the file.')
    group.add_argument('-d', '--directory', type=str, help='Send path to the directory. --not yet implemented')
    args = parser.parse_args()

    if args.filepath:
        filepaths = args.filepath
    else:
        src = libs.window.file_choose_dialog(True)
        filepaths = src[0]

    valid_filepath, not_found_list, directory_list, not_png_list = check_files(filepaths)

    if not_found_list:
        print('\n'.join(not_found_list))
        print('These files are not found')
        print('Go ahead make my day.\n')
    if directory_list:
        print('\n'.join(directory_list))
        print('This is directory')
        print('Do I have to start explaining the difference between files and directories?\n')
    if not_png_list:
        print('\n'.join(not_png_list))
        print('These files are not PNG images.')
        print("You'd better to learn or relearn what a PNG file is.\n")
    if not valid_filepath:
        print('There is no valid file to parse')
        print("It's all thanks to you there's no work to do :))")
        sys.exit()
    print('a hoy!!!!')
    libs.window.result_window(filepaths)
