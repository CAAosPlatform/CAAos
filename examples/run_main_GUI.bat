@echo off
setlocal

rem Move to the project folder, even when launched from a shortcut.
cd /d "%~dp0.."
rem Add the package source folder so the GUI can import the project modules.
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

rem Use the first argument as the Conda environment name; default to CAAos.
rem Example: examples\run_main_GUI.bat my-environment
set "CONDA_ENV=%~1"
if not defined CONDA_ENV set "CONDA_ENV=CAAos"

rem Check that Conda is available before trying to activate the environment.
where conda >nul 2>nul
if errorlevel 1 (
    echo Conda was not found. Add Anaconda or Miniconda to PATH and try again.
    pause
    exit /b 1
)

rem Activate the selected environment so its Python and dependencies are used.
call conda activate "%CONDA_ENV%"
if errorlevel 1 (
    echo Could not activate the Conda environment "%CONDA_ENV%".
    echo Usage: %~nx0 [environment-name]
    pause
    exit /b 1
)

rem Confirm Python is available in the activated environment.
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 and ensure it is on PATH.
    pause
    exit /b 1
)

rem Start the GUI entry point from this folder.
python "%~dp0main_GUI.py"
exit /b %errorlevel%
