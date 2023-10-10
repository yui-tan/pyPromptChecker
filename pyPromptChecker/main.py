# -*- coding: utf-8 -*-

import sys
import argparse

from gui import config
from window import from_main, check_files, find_target


def main():
    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog.')
    parser.add_argument('filepaths', metavar='Filepath', type=str, nargs='*', help='Send path to files and directories.')
    args = parser.parse_args()
    filepaths = []

    if args.filepaths:
        parameters = args.filepaths
    elif args.ask:
        parameters = from_main('directory')
    else:
        parameters = from_main('files')

    if parameters:
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

        from_main('window', valid_filepath)

    else:
        print('Cancelled!')


if __name__ == '__main__':
    main()
