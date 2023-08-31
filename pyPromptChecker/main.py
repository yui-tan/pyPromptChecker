# -*- coding: utf-8 -*-

import os
import sys
import argparse
import glob

from pyPromptChecker.lib import decoder
from pyPromptChecker.gui import window


def is_directory_check(filepaths):
    filepath_list = []
    if filepaths:
        for filepath in filepaths:
            if os.path.isdir(filepath):
                file_in_directory = directory_to_filelist([filepath])
                filepath_list = filepath_list + file_in_directory
        filepaths = filepaths + filepath_list
    return filepaths


def directory_to_filelist(directory_path):
    if not os.path.isdir(directory_path[0]):
        print('This is not a directory')
        sys.exit()
    directory = os.path.join(directory_path[0], '*')
    file_list = glob.glob(directory)
    return file_list


def check_files(target_list):
    file_counts = len(target_list) if target_list else 0
    progress_bar = None
    file_is_not_found_list = []
    this_is_directory_list = []
    this_file_is_not_image_file_list = []
    valid_file_list = []

    if file_counts > 5:
        app, progress_bar = window.from_main('progress')
        progress_bar.setLabelText("Checking files...")
        progress_bar.setRange(0, file_counts)

    for filepath in target_list:
        if not os.path.exists(filepath):
            file_is_not_found_list.append(filepath)
            if progress_bar:
                progress_bar.update_value()
            continue

        elif not os.path.isfile(filepath):
            this_is_directory_list.append(filepath)
            if progress_bar:
                progress_bar.update_value()
            continue

        result = decoder.image_format_identifier(filepath)

        if not result:
            this_file_is_not_image_file_list.append(filepath)
        else:
            valid_file_list.append(result)

        if progress_bar:
            progress_bar.update_value()

    if progress_bar:
        progress_bar.close()

    return valid_file_list, file_is_not_found_list, this_is_directory_list, this_file_is_not_image_file_list


def main(test=False):
    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog.')
    group.add_argument('-f', '--filepath', nargs='*', type=str, help='Send path to the file.')
    group.add_argument('-d', '--directory', type=str, help='Send path to the directory.')
    parser.add_argument('filepaths', metavar='Filepath', type=str, nargs='*', help='Send path to files and directories.')
    args = parser.parse_args()

    if args.filepath:
        filepaths = args.filepath
    elif args.filepaths or test:
        filepaths = args.filepaths
        filepaths = is_directory_check(filepaths)
    elif args.directory:
        filepaths = directory_to_filelist([args.directory])
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
        if directory_list:
            print('\n'.join(directory_list))
            print('This is directory')
        if not_png_list:
            print('\n'.join(not_png_list))
            print('These files are not supported image files.')
        if not valid_filepath:
            print('There is no valid file to parse')
            sys.exit()
        print('a hoy!!!!')
        valid_filepath.sort()
        window.from_main('result', valid_filepath)
    else:
        print('Cancelled!')


if __name__ == '__main__':
    main()
