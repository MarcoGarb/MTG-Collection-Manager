@echo off
rem start.bat - convenience launcher for MTG-Collection-Manager (Windows)
rem Places this file in the project root next to run.py and requirements.txt

:: Move to script directory (project root)
cd /d "%~dp0"

:use_active_env
if defined VIRTUAL_ENV (
    echo Using active virtual environment: %VIRTUAL_ENV%
    python "%~dp0run.py" %*
    goto :EOF
)

:find_known_venv
set "FOUNDVENV="
for %%V in (".venv" "venv" "env" "Env" ".env") do (
    if exist "%~dp0%%~V\Scripts\python.exe" (
        set "FOUNDVENV=%%~V"
        goto :activate_found_venv
    )
)

:activate_found_venv
if defined FOUNDVENV (
    echo Activating virtual environment: %FOUNDVENV%
    call "%~dp0%FOUNDVENV%\Scripts\activate.bat"
    python "%~dp0run.py" %*
    goto :EOF
)

:: No known venv found. Optionally create .venv with the py launcher.
if "%SKIP_CREATE_VENV%"=="1" goto :try_system_python

:try_create_venv
py -3 -V >nul 2>&1
if %ERRORLEVEL%==0 (
    echo No virtual environment detected. Creating one at "%.venv" (first-time only).
    py -3 -m venv "%~dp0.venv"
    if exist "%~dp0.venv\Scripts\activate.bat" (
        call "%~dp0.venv\Scripts\activate.bat"
        if exist "%~dp0requirements.txt" (
            echo Installing Python requirements (this may take a while)...
            pip install -r "%~dp0requirements.txt"
        ) else (
            echo No requirements.txt found — skipping pip install.
        )
        python "%~dp0run.py" %*
        goto :EOF
    ) else (
        echo Failed to create or locate the created venv. Continuing to system Python fallback.
    )
) else (
    echo The "py" launcher was not found. Trying system-wide python next.
)

:: Fallback to system python
:try_system_python
python -V >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Running with system python.
    python "%~dp0run.py" %*
    goto :EOF
)

:: Nothing worked
echo ERROR: No suitable Python interpreter found. Install Python 3 (and optionally the "py" launcher) or create a virtual environment named ".venv", "venv" or "env" in the project root.
echo You can set SKIP_CREATE_VENV=1 to avoid automatic venv creation.
exit /b 1
