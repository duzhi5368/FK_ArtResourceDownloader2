rm -fr dist build GUI/__pycache__
pyinstaller --name FKArtResourceDownloader --onefile --icon=Res/icon.png --windowed ./GUI/__main__.py