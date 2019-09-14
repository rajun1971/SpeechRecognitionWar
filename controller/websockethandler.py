# -*- coding: utf-8 -*-
# 標準ライブラリ
import urllib

# from pip
from logzero import logger
import tornado.websocket
import numpy as np

import model


class WebSocketHandler(tornado.websocket.WebSocketHandler):
#    CORS_ORIGINS = ['localhost', '127.0.0.1']

    # CORSチェックメソッド。これを実装しないとフレームワークが403を返す
    def check_origin(self, origin):
        return True
#        logger.info('check_origin:Enter')
#        parsed_origin = urllib.parse.urlparse(origin)
#        logger.debug(f'host name={parsed_origin.hostname}')
#        return parsed_origin.hostname in self.CORS_ORIGINS

    def open(self, session_id):
        logger.info(f'open:Enter(token={session_id})')
        self._session_id = session_id
        self._response = {}
        model.SessionCollector().SetPropertyInSession(
            session_id, {'instance': self})

    def on_message(self, message):
        items = model.SessionCollector().GetPropertyInSession(
            self._session_id)['transcoders'].items()
        for key, transcoder in items:
            transcoder.write_stream(np.frombuffer(message, dtype='float32'))
            if(transcoder.transcript):
                if(transcoder.transcript != self._response.get(key)):
                    self._response[key] = transcoder.transcript
                    self.write_message(self._response)

    def on_close(self):
        logger.info('on_close:Enter')
        model.SessionCollector().DeleteSession(self._session_id)
