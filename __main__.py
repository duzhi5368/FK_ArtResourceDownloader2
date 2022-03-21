from email.policy import default
import click

from FKArtResourceDownloader.Utils.FKLogger import FKLogger
from FKArtResourceDownloader.Core.FKDownloader import FKDownloader

@click.group('downloader')
def entry():
    pass

@click.argument('url')
@click.option('--proxy', default=None, type=click.STRING)
@entry.command('artstation-user', help='从 ArtStation 按用户下载')
def DownloadArtStationByUser(url, proxy):
    # todo
    return

def main():
    entry()

if __name__ == "__main__":
    main()