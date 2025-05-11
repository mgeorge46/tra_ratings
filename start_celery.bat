@echo off

REM Set project directory
set PROJECT_DIR=D:\Dev\Django\tra_ratings

REM Start Celery Worker
start cmd /k "cd /d %PROJECT_DIR% && workon ratings && celery -A tra_ratings worker --loglevel=info"

REM Start Celery Beat
start cmd /k "cd /d %PROJECT_DIR% && workon ratings && celery -A tra_ratings beat --loglevel=info"

REM Start Celery Flower
start cmd /k "cd /d %PROJECT_DIR% && workon ratings && celery -A tra_ratings flower --port=5555"
