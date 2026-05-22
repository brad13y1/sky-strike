@echo off
echo ================================
echo  Sky Strike - Build and Deploy
echo ================================
echo.

:: Step 1 - Delete old tar.gz from docs to prevent pygbag bundling it
echo [1/3] Cleaning old build from docs...
if exist docs\sky_strike.tar.gz del docs\sky_strike.tar.gz
echo Done.
echo.

:: Step 2 - Run pygbag
echo [2/3] Running pygbag build...
cd /d "C:\Users\dev_station\Desktop\Kanoa Projects\Sky_Strike"
pygbag --archive .
echo.

:: Step 3 - Copy ONLY the tar.gz to docs
echo [3/3] Copying tar.gz to docs...
copy build\web\sky_strike.tar.gz docs\
echo.

echo ================================
echo  Build complete!
echo  Now bump service-worker.js
echo  version, then commit and push
echo  via GitHub Desktop.
echo ================================
pause
