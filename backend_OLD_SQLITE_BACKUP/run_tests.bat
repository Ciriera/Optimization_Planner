@echo off
set PYTHONPATH=%~dp0
pytest --verbose --cov=app --cov-report=term-missing --cov-report=html 