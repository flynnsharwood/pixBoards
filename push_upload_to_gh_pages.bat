cd c:/Users/ggggg/root/personalScripts/apps_i_made/python/masonryBoard_v2
python3 cli.py --upload

git add . 
git commit -m "changes"
mshta "javascript:alert('choose the flynnshawoord option!');close();"

git push origin master

pyinstaller --onefile __main__.py -n boards
if exist boards.exe del /f /q boards.exe
move /Y dist\boards.exe binaries\boards.exe

cd "C:\Users\ggggg\Desktop\boardsUpload"

git add . 
git commit -m "changes"

mshta "javascript:alert('choose the boards sites option!');close();"
git push