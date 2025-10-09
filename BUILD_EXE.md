Building a single-file Windows executable (EXE)
===============================================

This project includes a helper PowerShell script `build_exe.ps1` that creates a single-file Windows executable using PyInstaller. The script creates an isolated virtual environment at `.build_env`, installs requirements and PyInstaller, and produces a one-file exe in `dist\`.

Quick steps (PowerShell):

1. Open PowerShell in the project root (where `run.py` is).
2. If your system restricts scripts, run with ExecutionPolicy bypass:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

3. If you already installed project requirements inside the build venv and only want to rebuild the exe, run:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\build_exe.ps1 -NoInstall
```

Result
------
- The executable will be at `dist\MTG-Collection-Manager.exe`.
- The script includes the `data` folder into the bundle by default. If your application needs additional asset folders, edit `build_exe.ps1` and add more `--add-data` arguments.

Notes & caveats
----------------
- The built EXE is a one-file bundle. At runtime PyInstaller extracts a temporary folder, so antivirus scanners may flag it; if this happens, build a folder-based distribution instead (remove `--onefile`).
- If your app spawns other scripts or relies on editable packages, you might need to adapt the PyInstaller spec or include hidden imports.
- For GUI apps replace `--console` with `--windowed` in `build_exe.ps1`.

Troubleshooting
---------------
- If the script fails to find Python, install Python 3 and ensure either the `py` launcher or `python` is available on PATH.
- If some imports are missing at runtime, PyInstaller may need explicit `--hidden-import` flags. Inspect the PyInstaller logs (in the `build` folder) to find missing modules and add them to `specArgs` in `build_exe.ps1`.

If you want, I can run the build script here to verify it completes in your environment, or modify it to create a ZIP containing the exe and a small README. Let me know which you prefer.