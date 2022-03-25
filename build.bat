python3 -m pip install -r requirements.txt
rm -fr dist build GUI/__pycache__
rmdir /s dist build __pycache__
pyinstaller --name FKArtResourceDownloader --onefile --icon=Res/icon.ico --windowed ./__main__.py
pause