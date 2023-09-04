# -*- coding: utf-8 -*-

import os
import sys
import argparse

from pyPromptChecker.lib import decoder
from pyPromptChecker.gui import window
from pyPromptChecker.gui import config


def find_target(root, depth):
    filepaths = []

    def _directory_search(current_dir, current_depth):
        if current_depth <= depth and os.path.exists(current_dir):
            for filename in os.listdir(current_dir):
                fullpath = os.path.join(current_dir, filename)
                if os.path.isfile(fullpath):
                    filepaths.append(fullpath)
                elif os.path.isdir(fullpath):
                    _directory_search(fullpath, current_depth + 1)
        else:
            return

    for path in root:
        if os.path.isfile(path):
            filepaths.append(path)
        else:
            _directory_search(path, 0)

    return filepaths


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


def main():
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
        parameters = args.filepath
    elif args.filepaths:
        parameters = args.filepaths
    elif args.directory:
        parameters = [args.directory]
    elif args.ask:
        parameters = window.from_main('directory')
    else:
        parameters = window.from_main('files')

    depth = config.get('SubDirectoryDepth', 0)
    filepaths = find_target(parameters, depth)

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
