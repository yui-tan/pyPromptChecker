@echo off
setlocal

set directory=%~dp0
for %%1 in ("%directory:~0,-1%") do set current=%%~nx1
if not "%current%" == "pyPromptChecker" (
	echo This script should be executed in the "pyPromptChecker" directory.
	exit /b 1
)

python --version > NUL 2>&1
if errorlevel 1 (
	echo Python 3 is not installed.
	exit /b 1
)

pip install virtualenv
python -m pip install --upgrade pip

if not exist "venv" (
	echo Installing venv...
	python -m venv venv
)

echo activating venv...
call ./venv/Scripts/activate

echo Installing pyPromptChecker...
pip install -e.

echo Making bat files...
md bat

echo @echo off>>bat/start.bat
echo @if not "%%~0"=="%%~dp0.\%%~nx0" start /min cmd /c,"%%~dp0.\%%~nx0" %%* ^& goto :eof>>bat/start.bat
echo cd ..>>bat/start.bat
echo call ./venv/Scripts/activate ^&^& mikkumiku>> bat/start.bat

echo @echo off>>bat/select_directory.bat
echo @if not "%%~0"=="%%~dp0.\%%~nx0" start /min cmd /c,"%%~dp0.\%%~nx0" %%* ^& goto :eof>>bat/select_directory.bat
echo cd ..>>bat/select_directory.bat
echo call ./venv/Scripts/activate ^&^& mikkumiku --ask>> bat/select_directory.bat

echo @echo off>>bat/drop_files.bat
echo @if not "%%~0"=="%%~dp0.\%%~nx0" start /min cmd /c,"%%~dp0.\%%~nx0" %%* ^& goto :eof>>bat/drop_files.bat
echo cd ..>>bat/drop_files.bat
echo call ./venv/Scripts/activate ^&^& mikkumiku -f %%*>> bat/drop_files.bat

echo @echo off>>bat/drop_directories.bat
echo @if not "%%~0"=="%%~dp0.\%%~nx0" start /min cmd /c,"%%~dp0.\%%~nx0" %%* ^& goto :eof>>bat/drop_directories.bat
echo cd ..>>bat/drop_directories.bat
echo call ./venv/Scripts/activate ^&^& mikkumiku -d %%1>> bat/drop_directories.bat

echo Now Installation is finished.
echo In a new directory "PyPromptChecker/bat", four files have been created.
echo The following are the four files:
echo.
echo start.bat:
echo When you run this file, a file selection dialog will appear,
echo and once a file is selected, processing will begin.
echo This is same as running command 'mikkumiku'
echo.
echo select_directory.bat:
echo When you run this file, a directory selection dialog will appear,
echo and once a directory is selected, processing will begin.
echo This is same as running command 'mikkumiku --ask'
echo.
echo drop_files.bat:
echo By creating a shortcut to this batch file,
echo you can start the processing by dragging and dropping a file onto the shortcut.
echo This is same as running command 'mikkumiku --filepath ...'
echo.
echo drop_directories.bat:
echo By creating a shortcut to this batch file,
echo you can start the processing by dragging and dropping a directory onto the shortcut.
echo This is same as running command 'mikkumiku --directory ...'
echo.
echo If you are unsure of what these batch files do by looking at their contents, please refrain from moving or editing them.

pause
exit/b 0
