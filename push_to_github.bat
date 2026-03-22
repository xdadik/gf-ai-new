@echo off
REM GitHub Push Script for Nova AI (Windows)
REM =========================================
REM PRIVACY WARNING: You previously asked to keep this code PRIVATE
REM This script will push to GitHub. Make sure:
REM 1. Your .env file is in .gitignore (it is)
REM 2. Your repo is PRIVATE if you want privacy
REM 3. Review the .gitignore file before pushing

echo.
echo ==========================================
echo     Nova AI GitHub Push Script
echo ==========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Check if git is initialized
if not exist .git (
    echo Initializing git repository...
    git init
    echo.
    echo You need to add your GitHub remote:
    echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    echo.
    pause
    exit /b 1
)

REM Check remote
echo Checking remote...
git remote -v
echo.

REM Check .gitignore
echo Checking .gitignore protections...
findstr /C:"personalities.py" .gitignore >nul 2>&1 && (
    echo    OK: personalities.py is protected
) || (
    echo    WARNING: personalities.py is NOT in .gitignore!
)

findstr /C:".env" .gitignore >nul 2>&1 && (
    echo    OK: .env is protected
) || (
    echo    WARNING: .env is NOT in .gitignore!
)
echo.

REM Add files
echo Adding files to git...
git add .
echo.

REM Check status
echo Git status:
git status -s
echo.

REM Commit
set /p commit_msg="Enter commit message: "
if "%commit_msg%"=="" set commit_msg=Update Nova AI - %date%

git commit -m "%commit_msg%"
echo.

REM Push
set /p push_confirm="Push to origin main? (y/N): "
if /I "%push_confirm%"=="y" (
    echo.
    echo Pushing to GitHub...
    git push origin main
    echo.
    echo Push complete!
) else (
    echo.
    echo Push cancelled.
    echo You can push manually later with: git push origin main
)

echo.
echo Next steps:
echo    - Check your repo on GitHub
echo    - Verify no sensitive files were pushed
echo    - If you see secrets, REMOVE THEM IMMEDIATELY
echo.
pause
