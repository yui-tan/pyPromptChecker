import os
import subprocess
import sys
import argparse

from tkinter import messagebox
import tkinter as tk

PACKAGE_DIRECTORY = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'pyPromptChecker')
OS = os.name


if __name__ == '__main__':

    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog.')
    parser.add_argument('filepaths', metavar='Filepath', type=str, nargs='*',
                        help='Send path to files and directories.')
    args = parser.parse_args()

    if args.filepaths:
        parameters = ' '.join(args.filepaths)
    elif args.ask:
        parameters = '--ask'
    else:
        parameters = None

    venv_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'pyPromptChecker/venv')

    if OS == 'posix':
        cmd = 'source ' + os.path.join(venv_dir, 'bin/activate')
    elif OS == 'nt':
        cmd = os.path.join(venv_dir, 'Scripts/activate.bat')
    else:
        print('Unsupported OS.')
        sys.exit()

    try:
        result = subprocess.check_output(cmd + ' && pip show pyPromptChecker', shell=True)
    except subprocess.CalledProcessError:
        result = None

    if not os.path.isdir(venv_dir):
        window = tk.Tk()
        window.withdraw()

        result_message = messagebox.showinfo('Installation', 'This is first time.\nStarting installation.')

        if result_message == 'ok':
            subprocess.run('python -m venv ' + venv_dir, shell=True)
            subprocess.run(cmd + ' && pip install --upgrade pip', shell=True)
            subprocess.run(cmd + ' && pip install -e.', shell=True)
            messagebox.showinfo('Installation', 'Installation is completed!')
            window.destroy()
        else:
            sys.exit()

        window.mainloop()

        result = True

    if not result:
        window = tk.Tk()
        window.withdraw()
        tk.messagebox.showinfo('Error', 'Error occurred.')
        sys.exit()
    else:
        subprocess.run(cmd + ' && pip install --upgrade pip', shell=True)

    if parameters:
        cmd = cmd + ' && mikkumiku ' + parameters
    else:
        cmd = cmd + ' && mikkumiku'

    subprocess.run(cmd, shell=True, executable='/bin/bash' if OS == 'posix' else None)
