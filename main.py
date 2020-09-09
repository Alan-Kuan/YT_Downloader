#!/usr/bin/env python3
# coding: utf-8

#      YT Downloader - A simple GUI for Python package, youtube-dl.
#      Copyright (C) 2019, 2020 Alan Kuan
#
#	   This file is a part of YT Downloader.
#  
#      YT Downloader is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#  
#      YT Downloader is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with YT Downloader.  If not, see <https://www.gnu.org/licenses/>.

import sys

from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QMessageBox, QLabel
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
from PyQt5.uic import loadUi

from youtube_dl import YoutubeDL

import urllib

import re

class Logger(QObject):
    msg_signal = pyqtSignal(str)
    def debug(self, msg):
        pass
        #print(msg)
    def warning(self, msg):
        print(msg)
    def error(self, msg):
        print('[YT Downloader]', msg)
        self.msg_signal.emit(msg)

class AppWindow(QDialog):

    def __init__(self):
        super(AppWindow, self).__init__()

        # load interface
        loadUi('interface.ui', self)

        # hide progress bar
        self.progress_bar.setHidden(True)

        # initialize buttons
        self.select_path_btn.clicked.connect(self.onSelectPath)
        self.confirm_btn.clicked.connect(self.onConfirm)
        self.download_btn.clicked.connect(self.onDownload)
        
    def clearContents(self):
        self.thumbnail.clear()
        self.title.setText("影片名稱")
        self.duration.setText("影片長度")
        self.uploader.setText("上傳者")
        self.upload_date.setText("上傳日期")
        self.description.setPlainText("")
        
    def download_vid(self, url, options):
        logger = Logger()
        logger.msg_signal.connect(self.onErrorOccur)
        options['logger'] = logger
        with YoutubeDL(options) as ydl:
            try:
                ydl.download([url])
            except:
                self.clearContents()

    def extract_info(self, url):
        logger = Logger()
        logger.msg_signal.connect(self.onErrorOccur)
        options = {
            'logger': logger,
            'progress_hooks': [self.progress_hook]
        }

        with YoutubeDL(options) as ydl:
            try:
                self.clearContents()

                info = ydl.extract_info(url, download = False)

                self.title.setText("影片名稱：" + info['title'])

                duration = info['duration']
                formatted_duration = []
                for i in range(3):
                    item = duration % 60
                    formatted_duration.append("{:02d}".format(item))
                    duration //= 60
                self.duration.setText("影片長度: " + formatted_duration[2] + ":" + formatted_duration[1] + ":" + formatted_duration[0])
                
                self.uploader.setText("上傳者: " + info['uploader'])
                
                date = info['upload_date']
                formatted_date = date[0:4] + "/" + date[4:6] + "/" + date[6:8]
                self.upload_date.setText("上傳日期: " + formatted_date)
                
                self.description.setPlainText(info['description'])
                
                img = QImage()
                data = urllib.request.urlopen(info['thumbnail']).read()
                img.loadFromData(data)
                self.thumbnail.setPixmap(QPixmap(img).scaledToWidth(320))
            except:
                self.clearContents()

    @pyqtSlot(dict)
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            val = d['_percent_str'][:-1]
            self.progress_bar.setValue(float(val))
        elif d['status'] == 'finished':
            self.progress_bar.setValue(100)

    @pyqtSlot()
    def onSelectPath(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.selected_path.setText(path)
    
    @pyqtSlot(str)
    def onErrorOccur(self, msg):
        # The following line is the best answer from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
        ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        QMessageBox.about(self, "Error", ansi_esc.sub('', msg))
 
    @pyqtSlot()
    def onConfirm(self):
        url = self.URL_input.text()
        self.extract_info(url)
            
    @pyqtSlot()
    def onDownload(self):
        url = self.URL_input.text()
        vid_format = self.format.currentText()
        path = self.selected_path.text() + '/%(title)s.%(ext)s'
        if vid_format == "mp3":
            options = {
                'format': 'bestaudio/best',
                'outtmpl': path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
        else:
            options = {
                'format': 'best',
                'outtmpl': path
            }
        self.progress_bar.setHidden(False)
        self.download_vid(url, options)
        print("[YT Downloader] Downloaded successfully!")
        QMessageBox.about(self, "Notification", "Downloaded successfully!")
        self.progress_bar.setHidden(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())
