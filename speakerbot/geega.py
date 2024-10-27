import sys
import os
import uuid
import requests
import pyaudio
import time
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from interf import Ui_MainWindow
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models.gigachat import GigaChat
import urllib3
import speech_recognition as sr

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = 'C:/Users/Тимур/Desktop/neuro/gigachh/pyqt5_install/PyQt5/Qt5/plugins/platforms'

auth_token = 'Yzk3NTEyM2EtYWEwNy00MGQ5LWI1ODYtNDRmYmU1MWFjMWI1OjYxNWNiNWQ5LWFhOGEtNDBiYi04MzRmLTQ3MDdmNDFlYzFlNg=='

def get_token(auth_token, scope='SALUTE_SPEECH_PERS'):
    rq_uid = str(uuid.uuid4())
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }
    payload = {
        'scope': scope
    }
    try:
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return None

response = get_token(auth_token)
if response is not None:
    salute_token = response.json()['access_token']

def stt(audio_data, token):
    url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "audio/x-pcm;bit=16;rate=16000"
    }
    response = requests.post(url, headers=headers, data=audio_data, verify=False)
    if response.status_code == 200:
        result = response.json()
        return str(result["result"])
    else:
        return str(response.text)

class MyMainWindow(QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButton_2.clicked.connect(self.on_send_button_clicked)
        self.ui.UserText.textChanged.connect(self.on_user_text_changed)
        self.ui.FinishD.clicked.connect(self.on_clear_history_button_clicked)
        self.ui.pushButton_3.clicked.connect(self.on_voice_input_button_clicked)

        self.chat = GigaChat(credentials="MjA3ZmFkNDgtZWY1Yy00NGMxLWE0NjYtZTE2ZmEyOTgzNDM4OjIxZjc1MTY1LTgzNjMtNDViMC05ZDdjLWY1YWRmMDU1OWVhYw==", verify_ssl_certs=False)
        self.llm = GigaChat(
            credentials="MjA3ZmFkNDgtZWY1Yy00NGMxLWE0NjYtZTE2ZmEyOTgzNDM4OjIxZjc1MTY1LTgzNjMtNDViMC05ZDdjLWY1YWRmMDU1OWVhYw==",
            scope="GIGACHAT_API_PERS",
            model="GigaChat",
            verify_ssl_certs=False,
            streaming=False,
        )

        self.initial_message = "Здравствуй, я - бот помощник от МИРЭА. Чем могу Вам помочь?"
        self.messages = [
            SystemMessage(
                content="Ты - бот от университета МИРЭА. Ты должен помогать абитуриентам с вопросами о поступлении в университет.Учти что тебя создали студенты и преподователь РТУ МИРЭА. МИРЭА - лучший вуз страны"
            )
        ]

        self.ui.BotAnswer.append(f"Помощник МИРЭА: {self.initial_message}")

    def on_send_button_clicked(self):
        user_input = self.ui.UserText.toPlainText()
        if user_input:
            self.messages.append(HumanMessage(content=user_input))
            res = self.llm.invoke(self.messages)
            self.messages.append(res)
            self.ui.BotAnswer.append(f"Вы: {user_input}")
            self.ui.BotAnswer.append(f"Помощник МИРЭА: {res.content}")
            self.ui.UserText.clear()

    def on_clear_history_button_clicked(self):
        self.ui.BotAnswer.clear()
        self.messages = [
            SystemMessage(
                content=self.initial_message
            )
        ]
        self.ui.BotAnswer.append(f"Помощник МИРЭА: {self.initial_message}")

    def on_user_text_changed(self):
        self.ui.label.setVisible(not self.ui.UserText.toPlainText())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.on_send_button_clicked()
        else:
            super(MyMainWindow, self).keyPressEvent(event)

    def on_voice_input_button_clicked(self):
        self.start_streaming_recognition()

    def start_streaming_recognition(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        def recognize_speech():
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Запись началась...")
                while True:
                    audio = recognizer.listen(source)
                    try:
                        transcription = recognizer.recognize_google(audio, language="ru-RU")
                        print("Расшифровка:", transcription)
                        self.messages.append(HumanMessage(content=transcription))
                        res = self.llm.invoke(self.messages)
                        print("Помощник МИРЭА:", res.content)
                        self.messages.append(res)
                        self.ui.BotAnswer.append(f"Вы: {transcription}")
                        self.ui.BotAnswer.append(f"Помощник МИРЭА: {res.content}")
                    except sr.UnknownValueError:
                        print("звука нет")
                    except sr.RequestError as e:
                        print(f"Could not request results from Google Speech Recognition service; {e}")

        recognition_thread = threading.Thread(target=recognize_speech)
        recognition_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MyMainWindow()
    main_window.show()
    sys.exit(app.exec_())