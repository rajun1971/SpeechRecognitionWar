# -*- coding: utf-8 -*-
"""
https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/microphone-speech-to-text.py
"""
import io
import threading
import queue

from watson_developer_cloud import SpeechToTextV1
from watson_developer_cloud.websocket import RecognizeCallback, AudioSource
import numpy as np
from logzero import logger

import model.key

cont_type = "audio/wav"
lang = "ja-JP_BroadbandModel"


def TranscodeFromFile(path, sample_rate):
    try:
        with io.open(path, 'rb') as audio_file:
            # watson connection
            stt = SpeechToTextV1(
                iam_apikey=model.key.WATSON_APIKEY, url=model.key.WATSON_URL)
            response = stt.recognize(
                audio=audio_file, content_type=cont_type, model=lang)
            result_json = response.result
            for i in range(len(result_json["results"])):
                logger.debug(
                    result_json["results"][i]["alternatives"][0]["transcript"])
            return result_json["results"][0]["alternatives"][0]["transcript"]
    except:
        return ""


# define callback for the speech to text service
class MyRecognizeCallback(RecognizeCallback):
    def __init__(self, parent):
        RecognizeCallback.__init__(self)
        self._parent = parent

    def on_transcription(self, transcript):
        logger.debug(f'on_transcription:{transcript}')
        self._parent.write_result(transcript[0]["transcript"])

    def on_connected(self):
        logger.debug('on_connected:Connection was successful')

    def on_error(self, error):
        logger.error(f'on_error:{error}')

    def on_inactivity_timeout(self, error):
        logger.debug(f'on_inactivity_timeout:{error}')

    def on_listening(self):
        logger.debug('on_listening:Service is listening')

    def on_hypothesis(self, hypothesis):
        logger.debug(f'on_hypothesis:{hypothesis}')
        self._parent.write_result(hypothesis)

    def on_data(self, data):
        logger.debug(f'on_data:{data}')

    def on_close(self):
        logger.debug("on_close:Connection closed")


class Transcoder:
    def __init__(self):
        logger.info('__init__:Enter')
        self._token = None
        self.transcript = None
        self._queue = queue.Queue()
        self._stt = SpeechToTextV1(
            iam_apikey=model.key.WATSON_APIKEY, url=model.key.WATSON_URL)
        self._audio_source = AudioSource(self._queue, True, True)
        # 2019/04/14現在、WebSocketのエンドポイントの証明書が不正扱いになっているので以下を設定する
        self._stt.disable_SSL_verification()

    def start(self, token):
        """Start up streaming speech call"""
        logger.info('start:Enter')
        self._token = token
        threading.Thread(target=self.process).start()

    def write_result(self, transcipt):
        self.transcript = transcipt

    def write_stream(self, buf):
        if(buf is None):
            self._queue.put(buf)
        else:
            arr = (buf * 32767).astype(np.int16)
            arr_bytes = arr.tobytes('C')
            self._queue.put(arr_bytes)

    def process(self):
        logger.info('process:Enter')
        mycallback = MyRecognizeCallback(self)
        logger.info('start transcode')
        self._stt.recognize_using_websocket(
            audio=self._audio_source,
            content_type='audio/l16; rate=16000',
            recognize_callback=mycallback,
            interim_results=True,
            model=lang)
        logger.info('end transcode')
