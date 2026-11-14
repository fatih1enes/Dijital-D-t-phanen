@echo off
chcp 65001 >nul
title Dijital Kutuphane
cd /d "%~dp0"

echo ================================================================
echo                     DIJITAL KUTUPHANE
echo ================================================================
echo.

:: 1. Python Komutu Kontrolu (python veya py)
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    py -3 --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    ) else (
        goto NOPYTHON
    )
)

:: 2. Ilk Calistirma Icin .env Dosyasi Kontrolu
if not exist "%~dp0.env" (
    echo [BILGI] Ilk calistirma tespit edildi. .env yapilandirmasi olusturuluyor...
    for /f "delims=" %%a in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')" 2^>nul') do set "RND_SECRET=%%a"
    if not defined RND_SECRET set "RND_SECRET=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%"
    (
        echo # Dijital Kutuphane Ortam Degiskenleri
        echo AUTO_OPEN_BROWSER=True
        echo ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
        echo MAX_UPLOAD_MB=250
        echo ACCESS_PASSWORD=
        echo COOKIE_SECURE=0
        echo SESSION_SECRET=%RND_SECRET%
    ) > "%~dp0.env"
)

:: 3. Sanal Ortam (VENV) Dizini Belirleme
set "VENV_DIR=%USERPROFILE%\.dijital_kutuphane_venv"
if exist "%~dp0.venv\Scripts\activate.bat" set "VENV_DIR=%~dp0.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" goto KURULUM
goto BASLAT

:KURULUM
echo [1/3] Ilk kurulum tespit edildi. Sanal ortam olusturuluyor...
echo Konum: %VENV_DIR%
%PYTHON_CMD% -m venv "%VENV_DIR%"
if errorlevel 1 goto VENVERROR

echo.
echo [2/3] Gerekli kutuphaneler yukleniyor. Lutfen bekleyin...
echo Bu islem internet baglantiniza bagli olarak 1-2 dakika surebilir.
call "%VENV_DIR%\Scripts\activate.bat"
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto PIPERROR
echo.
echo [OK] Kurulum basariyla tamamlandi!
echo.
goto BASLAT_UYGULAMA

:BASLAT
echo [1/2] Sanal ortam aktif ediliyor...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 goto ACTIVATEERROR

:: Tum kritik kutuphanelerin varligini dogrula (Eksik veya yeni eklenen paket kontrolu)
"%VENV_DIR%\Scripts\python.exe" -c "import fastapi, uvicorn, telethon, cryptg, aiosqlite, google.genai, pdfplumber, pydantic, PIL" >nul 2>&1
if errorlevel 1 (
    echo [GUNCELLEME] Eksik veya yeni eklenen kutuphaneler tespit edildi!
    echo Paketler kontrol ediliyor ve yukleniyor...
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 goto PIPERROR
    echo [OK] Kutuphaneler basariyla guncellendi!
    echo.
)

:BASLAT_UYGULAMA
echo [2/2] Dijital Kutuphane baslatiliyor...
echo.
echo ----------------------------------------------------------------
echo Tarayiciniz otomatik acilacaktir: http://localhost:8000
echo Kapatmak veya durdurmak icin bu pencereyi kapatabilirsiniz.
echo ----------------------------------------------------------------
echo.
set "AUTO_OPEN_BROWSER=True"
"%VENV_DIR%\Scripts\python.exe" "%~dp0main.py"
goto END

:NOPYTHON
echo.
echo ================================================================
echo [HATA] Python sisteminizde bulunamadi!
echo ================================================================
echo Dijital Kutuphane'yi calistirmak icin Python'in bilgisayarinizda
echo yuklu olmasi gerekmektedir.
echo.
echo Cozum Adimlari:
echo 1. https://www.python.org/downloads/ adresinden Python'i indirin.
echo 2. Kurulum basladiginda alttaki secenegi MUTLAKA ISARETLEYIN:
echo    "[X] Add python.exe to PATH"
echo 3. Kurulum bittikten sonra BASLAT.bat dosyasini tekrar calistirin.
echo ================================================================
echo.
pause
exit /b

:VENVERROR
echo.
echo ================================================================
echo [HATA] Sanal ortam olusturulamadi!
echo ================================================================
echo Python venv modulu calisirken bir hata ile karsilasti.
echo Python kurulumunuzun tam oldugundan emin olun.
echo.
pause
exit /b

:PIPERROR
echo.
echo ================================================================
echo [HATA] Paketler yuklenirken bir sorun olustu!
echo ================================================================
echo Lutfen internet baglantinizi kontrol edin ve dosyayi tekrar calistirin.
echo.
pause
exit /b

:ACTIVATEERROR
echo.
echo ================================================================
echo [HATA] Sanal ortam aktif edilemedi!
echo ================================================================
echo Sanal ortam bozulmus olabilir. Klasoru silip tekrar deneyin:
echo %VENV_DIR%
echo.
pause
exit /b

:END
pause
