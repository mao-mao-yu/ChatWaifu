import time
import sys
import threading
import langid
from PyQt5 import QtCore, QtGui, QtWidgets  # QtMultimedia
import pygame
import librosa
import chatgpt
from create_audio import CreateAudio
from configs.gui_config import *
import openai


class Ui(object):
    def __init__(self):
        openai.api_key = API_KEY
        self.model_path = MODEL_PATH
        self.config_path = CONFIG_PATH
        self.MODEL = CreateAudio(MODEL_PATH, CONFIG_PATH, model_type=MODEL_TYPE)
        self.audio_path = ""
        self.all_text = ALL_TEXT

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1100, 843)
        Form.setFixedSize(1100, 843)
        # 标题文字
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(390, 0, 311, 61))
        self.label.setStyleSheet("color:rgb(18, 0, 153);\n"
                                 "\n"
                                 "font: 75 25pt \"Segoe Print\";\n"
                                 "")
        self.label.setObjectName("label")

        # 背景
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(-350, 45, 1500, 843))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(r"H:\pyproj\vits\img\001.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")

        # 输入对话内容
        self.plainTextEdit = QtWidgets.QPlainTextEdit(Form)
        self.plainTextEdit.setGeometry(QtCore.QRect(60, 590, 411, 200))
        self.plainTextEdit.setObjectName("plainTextEdit")

        # 文字显示
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(60, 90, 411, 400))
        self.label_3.setStyleSheet("font: 14pt \"Arial\";background-color: rgba(255, 255, 255, 0.7);")
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName("label_3")

        # 发送按钮
        self.pushButton_6 = QtWidgets.QPushButton(Form)
        self.pushButton_6.setGeometry(QtCore.QRect(500, 670, 71, 71))
        self.pushButton_6.setStyleSheet("background-color: rgba(255, 255, 255, 0.5);")
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_6.clicked.connect(self.button)

        # 接收并保存到右边
        self.pushButton_7 = QtWidgets.QPushButton(Form)
        self.pushButton_7.setGeometry(QtCore.QRect(500, 420, 71, 71))
        self.pushButton_7.setStyleSheet("background-color: rgba(255, 255, 255, 0.5);")
        self.pushButton_7.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(r"H:\pyproj\vits\img\play1.png"))
        self.pushButton_7.setIcon(icon)
        self.pushButton_7.setIconSize(QtCore.QSize(50, 50))
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_7.clicked.connect(self.read_text)

        # 显示聊天记录框
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setGeometry(QtCore.QRect(695, 90, 350, 700))
        self.textBrowser.setStyleSheet("background-color: rgba(255, 255, 255, 0.7);")
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setText(ALL_TEXT)

        self.label.raise_()
        self.label_2.raise_()
        self.plainTextEdit.raise_()
        self.label_3.raise_()
        self.pushButton_6.raise_()
        self.pushButton_7.raise_()
        self.textBrowser.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "PAIMON CHATBOT"))
        self.label.setText(_translate("Form", "PaiMon ChatBot"))
        self.plainTextEdit.setPlaceholderText(_translate("Form", "Please enter text"))
        self.pushButton_6.setText(_translate("Form", "Sent"))
        Form.setWindowIcon(QtGui.QIcon(r'H:\pyproj\vits\img\paimon.ico'))

    def button(self):
        text = self.plainTextEdit.toPlainText()
        lang = langid.classify(text)[0]
        if lang.upper() == 'JA':
            speaker_index = 1
        elif lang.upper() == 'ZH':
            speaker_index = 0
        else:
            raise "Can't find index"
        if text == '':
            self.label_3.setText('Please enter text！')
        if self.MODEL is None:
            self.MODEL = CreateAudio(self.model_path, self.config_path, model_type=MODEL_TYPE)
        else:
            self.plainTextEdit.setPlainText('')
            prompt0 = text
            self.textBrowser.setText(self.all_text + '\nYou: ' + text)
            if CALL_NAME == '':
                res, self.all_text, audio_text = chatgpt.chat(self.all_text, prompt0)
            else:
                res, self.all_text, audio_text = chatgpt.chat(self.all_text, prompt0, call_name=CALL_NAME)
            self.label_3.setText(audio_text)
            self.textBrowser.setText(self.all_text)

            self.audio_path = self.MODEL.speak(audio_text, speaker_index=speaker_index)

    def read_text(self):
        if self.audio_path is None:
            raise print('Audio path is not exists')
        else:
            t = threading.Thread(target=play, args=(self.audio_path,))
            t.start()
            t.join()


def play(audio_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    timer = librosa.get_duration(filename=audio_path)
    time.sleep(timer)
    pygame.mixer.music.stop()
    pygame.quit()


class windows(QtWidgets.QWidget):
    def __init__(self):
        super(windows, self).__init__()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = windows()
    Widget = Ui()
    Widget.setupUi(Form)
    Form.show()
    app.exec()
