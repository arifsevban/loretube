@echo off
setlocal
chcp 65001 >nul
title TubeFlow
cd /d "%~dp0"

echo.
echo  TubeFlow baslatiliyor...
echo.

powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0create_desktop_shortcut.ps1" -ProjectDir "%~dp0."
if errorlevel 1 echo [UYARI] Masaustu kisayolu olusturulamadi; uygulama baslatilmaya devam edilecek.

set "PYTHON_LAUNCHER="
set "PYTHON_ARGS="

where py >nul 2>nul
if not errorlevel 1 (
    py -3.10 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_LAUNCHER=py"
        set "PYTHON_ARGS=-3.10"
    )
)

if not defined PYTHON_LAUNCHER (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
        if not errorlevel 1 (
            set "PYTHON_LAUNCHER=py"
            set "PYTHON_ARGS=-3"
        )
    )
)

if not defined PYTHON_LAUNCHER (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_LAUNCHER=python"
    )
)

if not defined PYTHON_LAUNCHER (
    where python3 >nul 2>nul
    if not errorlevel 1 (
        python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_LAUNCHER=python3"
    )
)

if not defined PYTHON_LAUNCHER (
    echo [HATA] Python 3.10 veya uzeri bulunamadi.
    echo Python 3.10+ kurun; kurulumda Python'i PATH'e ekleyin veya Python Launcher'i etkinlestirin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python bulundu: %PYTHON_LAUNCHER% %PYTHON_ARGS%

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Sanal ortam olusturuluyor...
    "%PYTHON_LAUNCHER%" %PYTHON_ARGS% -m venv .venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi.
        pause
        exit /b 1
    )
)

echo [2/3] Gerekli Python paketleri kontrol ediliyor...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [HATA] Paketler kurulamadi. Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo [3/4] FFmpeg kontrol ediliyor...
".venv\Scripts\python.exe" install_ffmpeg.py
if errorlevel 1 (
    echo [UYARI] FFmpeg otomatik kurulamadi. LoreFlow yine acilacak; MP3 donusumu kullanilamayabilir.
)

echo [4/4] LoreFlow aciliyor. Kapatmak icin Ctrl+C basin.
".venv\Scripts\python.exe" run.py
if errorlevel 1 (
    echo [HATA] TubeFlow baslatilamadi. Yukaridaki mesaji kontrol edin.
    pause
)
endlocal
