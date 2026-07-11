@echo off
set /p msg="请输入更新说明: "
git add .
git commit -m "%msg%"
git push origin main
if errorlevel 1 (
    echo 推送失败，请检查网络
    pause
)
