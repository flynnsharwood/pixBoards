call cd C:\Users\ggggg\root\personalScripts\apps_i_made\python\masonryBoard_v2
call python3 cli.py --config configs/pinterest.yml --random 100000
call python3 cli.py --config configs/pinterest.yml --upload --useSaved --random 100000
call cd C:\Users\ggggg\Desktop\pinterest_boards_upload
call git init
call git add .
call git config --local user.email "coerciasink+github2@gmail.com"
call git config --local user.name "boardsSites"
call git commit -m "semi-auto commit"
call git remote add origin https://github.com/boardsSites/pinterest.git
call git branch -M main
call git push --force