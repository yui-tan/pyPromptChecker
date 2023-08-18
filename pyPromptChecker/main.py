# -*- coding: utf-8 -*-

import os
import sys
import argparse
import glob

from lib import decoder
from gui import window


def directory_to_filelist(directory_path):
    if not os.path.isdir(directory_path[0]):
        print('This is not a directory')
        print("It's all thanks to you there's no work to do :))")
        sys.exit()
    directory = os.path.join(directory_path[0], '*')
    file_list = glob.glob(directory)
    return file_list


def check_files(target_list):
    file_counts = len(target_list) if target_list else 0
    progress_bar = None
    progress_enable = False
    file_is_not_found_list = []
    this_is_directory_list = []
    this_file_is_not_png_file_list = []
    valid_file_list = []

    if file_counts > 20:
        app, progress_bar = window.from_main('progress')
        progress_bar.setLabelText("Checking files...")
        progress_bar.setRange(0, file_counts)
        window.move_center(progress_bar)
        progress_enable = True

    for filepath in target_list:
        if not os.path.exists(filepath):
            file_is_not_found_list.append(filepath)
        elif not os.path.isfile(filepath):
            this_is_directory_list.append(filepath)
        elif not decoder.image_format_identifier(filepath):
            this_file_is_not_png_file_list.append(filepath)
        else:
            valid_file_list.append(filepath)
        if progress_enable:
            progress_bar.update_value()

    if progress_enable:
        progress_bar.close()

    return valid_file_list, file_is_not_found_list, this_is_directory_list, this_file_is_not_png_file_list


def main():
    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog.')
    group.add_argument('-f', '--filepath', nargs='*', type=str, help='Send path to the file.')
    group.add_argument('-d', '--directory', type=str, help='Send path to the directory.')
    args = parser.parse_args()

    if args.filepath:
        filepaths = args.filepath
    elif args.directory:
        filepaths = directory_to_filelist(args.directory)
    elif args.ask:
        src = window.from_main('directory')
        filepaths = directory_to_filelist(src) if src else None
    else:
        filepaths = window.from_main('files')

    if filepaths:
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
        valid_filepath.sort()
        window.from_main('result', valid_filepath)


if __name__ == '__main__':
    main()
