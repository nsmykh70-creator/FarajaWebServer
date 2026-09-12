@echo off
setlocal EnableExtensions
rem ============================================================
rem  Faraja WebServer V16 - ручная сборка PRO (как делает агент)
rem
rem  build.bat           - безопасная сборка в FarajaWebServerPRO_stage.exe
rem                        (не трогает запущенный PRO)
rem  build.bat PRO       - сборка + замена dist\FarajaWebServerPRO.exe
rem                        (требует закрытый PRO)
rem  build.bat check     - только проверка: компиляция + дымовой тест
rem ============================================================
echo Faraja WebServer V16 build

set "PY="
py -3.12 --version >nul 2>nul && set "PY=py -3.12"
if defined PY goto pyok
python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo [ERROR] Python not found. Ustanovite Python 3.12 x64.
  pause
  exit /b 1
)
:pyok
%PY% --version

if /i "%~1"=="check" goto check

rem --- 0. Проверка синтаксиса ---
echo.
echo [1/5] Proverka sintaksisa...
%PY% -m py_compile MiniServer.py
if errorlevel 1 (
  echo [ERROR] Oshibka sintaksisa v MiniServer.py
  pause
  exit /b 1
)
echo OK.

rem --- 1. Зависимости ---
echo.
echo [2/5] Zavisimosti...
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 goto fail

rem --- 2. Имя выходного файла ---
set "OUT=FarajaWebServerPRO_stage"
if /i "%~1"=="PRO" set "OUT=FarajaWebServerPRO"

rem --- 3. Если собираем PRO - проверяем, что он не запущен ---
if /i "%~1"=="PRO" (
  tasklist /fi "IMAGENAME eq FarajaWebServerPRO.exe" 2>nul | find /i "FarajaWebServerPRO.exe" >nul
  if not errorlevel 1 (
    echo [ERROR] FarajaWebServerPRO.exe zapushchen. Zakroyte ego i povtorite.
    pause
    exit /b 1
  )
)

rem --- 4. Чистый stage www (без мусора: downloads, runtime, exe, syslog) ---
echo.
echo [3/5] Stage www...
if exist .build_www rmdir /s /q .build_www
robocopy www .build_www /E /NFL /NDL /NJH /NJS >nul
if exist .build_www\downloads rmdir /s /q .build_www\downloads
if exist .build_www\runtime rmdir /s /q .build_www\runtime
del /q .build_www\*.exe 2>nul
del /q .build_www\*.zip 2>nul
del /q .build_www\MiniServer.py 2>nul

rem --- 5. Сборка (onefile, windowed, все ресурсы) ---
echo.
echo [4/5] Sborka %OUT%.exe ...
if exist build rmdir /s /q build
if exist "%OUT%.spec" del /q "%OUT%.spec"
%PY% -m PyInstaller --noconfirm --onefile --windowed --icon "assets\logo.ico" --name "%OUT%" --add-data "config;config" --add-data ".build_www;www" --add-data "assets;assets" --add-data "components.json;." --add-data "requirements.txt;." --clean MiniServer.py
if errorlevel 1 goto fail
rmdir /s /q .build_www

echo.
echo [5/5] Gotovo:
for %%F in ("dist\%OUT%.exe") do echo   %%~nxF  %%~zF bait
echo.
echo BUILD SUCCESSFUL - dist\%OUT%.exe
if /i not "%~1"=="PRO" (
  echo Podskazka: zakroyte PRO i zapustite 'build.bat PRO' chtoby zamenit ego,
  echo libo pereimenujte vruchnuyu: stage -^> FarajaWebServerPRO.exe
)
pause
exit /b 0

:check
echo.
echo Dymovoy test...
%PY% -u "%LOCALAPPDATA%\Temp\opencode\smoke_v16.py" 2>nul
if errorlevel 1 (
  echo [ERROR] Smoke test provalen
  pause
  exit /b 1
)
echo SMOKE OK
pause
exit /b 0

:fail
echo.
echo BUILD FAILED
pause
exit /b 1
