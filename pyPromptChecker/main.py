import os
import sys
import argparse
import glob
import pyPromptChecker

from pyPromptChecker.lib import decoder
from pyPromptChecker.lib import window


def directory_to_filelist(directory_path):
    if not os.path.isdir(directory_path):
        print('This is not a directory')
        print("It's all thanks to you there's no work to do :))")
        sys.exit()
    directory = os.path.join(directory_path, '*')
    file_list = glob.glob(directory)
    return file_list


def check_files(target_list):
    file_counts = len(target_list)
    progress_bar = None
    progress_enable = False
    file_is_not_found_list = []
    this_is_directory_list = []
    this_file_is_not_png_file_list = []
    valid_file_list = []

    if file_counts > 20:
        app, progress_bar = pyPromptChecker.lib.window.checking_progress(len(target_list))
        progress_bar.show()
        progress_enable = True

    for filepath in target_list:
        if not os.path.exists(filepath):
            file_is_not_found_list.append(filepath)
        elif not os.path.isfile(filepath):
            this_is_directory_list.append(filepath)
        elif not decoder.png_checker(filepath):
            this_file_is_not_png_file_list.append(filepath)
        else:
            valid_file_list.append(filepath)
        if progress_enable:
            progress_bar.update_bar()

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
        src = window.directory_choose_dialog(True)
        filepaths = directory_to_filelist(src)
    else:
        src = window.file_choose_dialog(True)
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
    valid_filepath.sort()
    window.result_window(valid_filepath)


if __name__ == '__main__':
    main()
