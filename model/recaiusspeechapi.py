# -*- coding: utf-8 -*-
"""Transcoder with TOSHIBA RECAIUS API."""
import threading
import queue
import time

import numpy as np
from logzero import logger
import requests

import model.key

AUTH_URL = 'https://api.recaius.jp/auth/v2/tokens'
VOICE_URL = 'https://api.recaius.jp/asr/v2/voices'


class Transcoder:
    """Transcoder Class."""

    def __init__(self):
        """Constructor."""
        logger.info('__init__:Enter')
        self._token = None
        self.transcript = None
        self._queue = queue.Queue()

    def start(self, token):
        """Start recognition."""
        logger.info('start:Enter')
        self._token = token
        threading.Thread(target=self._process).start()

    def write_stream(self, buf):
        """Write audio stream."""
        self._queue.put(buf)

    def _process(self):
        logger.info('_process:Enter')
        token = self._authenticate()['token']
        uuid = self._start_recognition(token)['uuid']
        logger.info('start transcode')
        i = 1
        while True:
            arr = self._stream_generator()
            if(arr is None):
                break
            # logger.debug(f'{len(arr)} , {self._queue.qsize()}')
            inline = np.hstack(arr)
            arr_bytes = inline.tobytes('C')
            header = {
                'Content-Type': 'multipart/form-data',
                'X-Token': token
            }
            files = {
                'voice_id': ('', i, ''),
                'voice': ('', arr_bytes, 'application/octet-stream')
            }
            resp = requests.put(
                f'{VOICE_URL}/{uuid}', headers=header, files=files)
            if(resp.status_code == 200):
                logger.debug(resp.json())
                result = resp.json()[0]
                if(result[0] == 'TMP_RESULT' or result[0] == 'RESULT'):
                    self._write_result(result[1])
            i = i + 1
        self._flush_recognition(uuid, token, i)
        while True:
            if(self._get_result(uuid, token) is None):
                break
            time.sleep(0.1)
        self._end_recognition(uuid, token)
        logger.info('end transcode')

    def _authenticate(self):
        speechrecog_jajp_id = model.key.RECAIUS_ID
        speechrecog_jajp_password = model.key.RECAIUS_PASSWORD
        param = {
            "speech_recog_jaJP": {
                'service_id': speechrecog_jajp_id,
                'password': speechrecog_jajp_password
            }
        }
        return requests.post(AUTH_URL, json=param).json()

    def _flush_recognition(self, uuid, token, i):
        header = {
            'Content-Type': 'application/json',
            'X-Token': token
        }
        param = {
            'voice_id': i,
        }
        resp = requests.put(
            f'{VOICE_URL}/{uuid}/flush', headers=header, json=param)
        if(resp.status_code == 200):
            logger.debug(f'frush result:{resp.json()}')
            return resp.json()
        else:
            logger.debug(f'flush result(status:{resp.status_code})')

    def _get_result(self, uuid, token):
        header = {
            'X-Token': token
        }
        resp = requests.get(f'{VOICE_URL}/{uuid}/results', headers=header)
        if(resp.status_code == 200):
            logger.debug(f'get result:{resp.json()}')
            return resp.json()
        else:
            logger.debug(f'get result(status:{resp.status_code})')

    def _stream_generator(self):
        arr = []
        while True:
            try:
                v = self._queue.get_nowait()
                # print(v)
                if v is None:
                    return None
                arr.append((v * 32767).astype(np.int16))
            except queue.Empty:
                if(len(arr) != 0):
                    break
                else:
                    time.sleep(0.1)
        return arr

    def _start_recognition(self, token):
        header = {
            'Content-Type': 'application/json',
            'X-Token': token
        }
        param = {
            'model_id': 1
        }
        return requests.post(VOICE_URL, headers=header, json=param).json()

    def _end_recognition(self, uuid, token):
        header = {
            'X-Token': token
        }
        resp = requests.delete(f'{VOICE_URL}/{uuid}', headers=header)
        if(resp.status_code == 204):
            logger.debug(f'delete result(status:{resp.status_code})')

    def _write_result(self, transcipt):
        self.transcript = transcipt
