REM call cd C:\Users\ggggg\root\personalScripts\apps_i_made\python\imgUploader
REM call python3 listFiles.py
REM call python3 fileListUpload.py
call cd C:\Users\ggggg\root\personalScripts\apps_i_made\python\masonryBoard_v2
call python3 cli.py --upload --useSaved --random 100000
call cd C:\Users\ggggg\Desktop\boards_v2_upload
call git init
call git config --local user.email "coerciasink+github2@gmail.com"
call git config --local user.name "boardsSites"
call git add .
call git commit -m "semi-auto commit"
call git remote add origin https://boardsSites@github.com/boardsSites/art.git
call git branch -M main
call git push --force