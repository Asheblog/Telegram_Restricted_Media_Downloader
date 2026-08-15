# coding=UTF-8
# Author:Gentlesprite
# Software:PyCharm
# Time:2024/9/5 19:08
# File:main.py
from module.bootstrap import initialize
from module.downloader import TelegramRestrictedMediaDownloader
from module.util import check_environ

if __name__ == "__main__":
    initialize()
    check_environ()
    trmd = TelegramRestrictedMediaDownloader()
    trmd.run()
