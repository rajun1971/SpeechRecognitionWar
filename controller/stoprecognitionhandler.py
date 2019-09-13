# -*- coding: utf-8 -*-
import tornado.web
from logzero import logger

import model


class StopRecognitionHandler(tornado.web.RequestHandler):
    def get(self, session_id):
        logger.info('get:Enter')
        tcs = model.SessionCollector().GetPropertyInSession(
            session_id)['transcoders']
        for transcoder in tcs.values():
            transcoder.write_stream(None)


"""
    import wave
    def _save_voice(self, voice):
        SAMPLE_SIZE = 2
        SAMPLE_RATE = 44100
        PATH = 'output.wav'
        with wave.open(PATH, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(SAMPLE_SIZE)
            wf.setframerate(SAMPLE_RATE)
            while True:
                # バイナリに16ビットの整数に変換して保存
                v = voice.get_nowait()
                if voice.empty():
                    break
                arr = (v * 32767).astype(np.int16)
                wf.writeframes(arr.tobytes('C'))
"""
