# -*- coding: utf-8 -*-
from logzero import logger
import tornado.web

import model


class CreateSessionHandler(tornado.web.RequestHandler):
    def get(self):
        logger.info('Enter:Create session API')
        # 音声認識のためのリソース作成
        session_id = model.SessionCollector().CreateSession()
        sp = {
            'transcoders': {
#                'recaius': model.recaiusspeechapi.Transcoder(),
                'gcp': model.googlespeechapi.Transcoder(),
                'azure': model.microsoftspeechapi.Transcoder(),
                'watson': model.watsonspeechapi.Transcoder(),
            }
        }
        model.session.SessionCollector().SetPropertyInSession(session_id, sp)
        self.write({'session_id': session_id})
