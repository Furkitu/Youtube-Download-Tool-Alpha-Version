@echo off
echo YouTube İndirme Aracı - Windows Kurulumu
echo ----------------------------------------

REM Python kurulu mu kontrol et
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadi. Lutfen Python'u kurun ve tekrar deneyin.
    pause
    exit /b
)

echo Bagimliliklar yukleniyor...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Uygulama insa ediliyor (EXE)...
echo.

REM CustomTkinter yolunu bul ve veriyi ekle
for /f "delims=" %%i in ('python -c "import customtkinter; print(customtkinter.__path__[0])"') do set CTK_PATH=%%i

pyinstaller --noconfirm --onedir --windowed --name "YouTubeIndirici" ^
    --add-data "%CTK_PATH%;customtkinter/" ^
    --icon=NONE ^
    main.py

echo.
echo -------------------------------------------------------
echo ISLEM TAMAMLANDI!
echo Uygulamaniz su klasorde: dist\YouTubeIndirici\YouTubeIndirici.exe
echo -------------------------------------------------------
pause
