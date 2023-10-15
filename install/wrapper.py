import os
import subprocess
import sys
import venv
import argparse


PACKAGE_DIRECTORY = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'pyPromptChecker')
OS = os.name

if __name__ == '__main__':

    description_text = 'Script for extracting and formatting PNG chunks.\n'
    description_text = description_text + 'If no options are specified, the script will open a file choose dialog.\n'
    description_text = description_text + 'All options are mutually exclusive.'
    parser = argparse.ArgumentParser(description=description_text, formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--ask', action='store_true', help='Open directory choose dialog.')
    parser.add_argument('filepaths', metavar='Filepath', type=str, nargs='*', help='Send path to files and directories.')
    args = parser.parse_args()

    if args.filepaths:
        parameters = ' '.join(args.filepaths)
    elif args.ask:
        parameters = '--ask'
    else:
        parameters = None

    venv_dir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'pyPromptChecker/venv')

    if not os.path.isdir(venv_dir):
        venv.create(venv_dir, with_pip=True)
        first_time_flag = True

    if OS == 'posix':
        venv_dir = os.path.join(venv_dir, 'bin/activate')
        cmd = 'source ' + venv_dir
    elif OS == 'nt':
        venv_dir = os.path.join(venv_dir, 'Scripts/activate.bat')
        cmd = venv_dir
    else:
        print('Unsupported OS.')
        sys.exit()

    try:
        result = subprocess.check_output(cmd + ' && pip show pyPromptChecker', shell=True)
    except subprocess.CalledProcessError:
        result = None

    if not result:
        os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
        subprocess.run(cmd + ' && pip install -e.', shell=True)

    if parameters:
        cmd = cmd + ' && mikkumiku ' + parameters
    else:
        cmd = cmd + ' && mikkumiku'

    subprocess.run(cmd, shell=True, executable='/bin/bash' if OS == 'posix' else None)
