setlocal EnableDelayedExpansion
echo .
set /p choice=push pixBoards or gh_pages or both? (1,2,3):

if "%choice%" == "1" (
	call :pixBoards
	goto end
) else if "%choice%" == "2" (
	call :gh_pages
	goto end
) else if "%choice%" == "3" (
	call :pixBoards
	call :gh_pages
	goto end
)

:end
echo.
pause
exit /b

:pixBoards
cd c:/Users/ggggg/root/personalScripts/apps_i_made/python/masonryBoard_v2
python3 main.py --upload --useSaved

git add . 
git commit -m "changes"
mshta "javascript:alert('choose the flynnshawoord option!');close();"

git push


:gh_pages
cd "C:\Users\ggggg\Desktop\boards_v2_upload"

git init
git remote add origin https://github.com/boardsSites/art.git
git add . 
git commit -m "changes"

mshta "javascript:alert('choose the boards sites option!');close();"
git push origin main