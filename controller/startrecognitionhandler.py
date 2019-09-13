# -*- coding: utf-8 -*-
import tornado.web
from logzero import logger

import model


class StartRecognitionHandler(tornado.web.RequestHandler):
    def get(self, session_id):
        logger.info('get:Enter')
        tcs = model.SessionCollector().GetPropertyInSession(
            session_id)['transcoders']
        for transcoder in tcs.values():
            transcoder.start(session_id)
