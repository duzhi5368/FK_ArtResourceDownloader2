python3 -m pip install -r requirements.txt
rm -fr dist build GUI/__pycache__
pyinstaller --name FKArtResourceDownloader --onefile --icon=Res/icon.png --windowed ./__main__.py