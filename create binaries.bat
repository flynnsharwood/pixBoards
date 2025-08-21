pyinstaller --onefile main.py -n boards
if exist boards.exe del /f /q boards.exe
move /Y dist\boards.exe binaries\boards.exe

rmdir /s /q dist
rmdir /s /q build
del /f /q boards.spec