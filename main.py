# -*- coding: utf-8 -*-
"""Speech to Textお試しWebサービス

GCP, Azure, Watson等々のCloud STTをまとめて試してみるサービスです。
サービスを立ち上げ、ブラウザからアクセスすると、ブラウザを立ち上げたPCのマイクを利用して音声入力し、各サービスでテキスト化されます。

事前に各サービスのTokenの取得、設定の必要があります。

Example:
    $ python main.py

Todo:
    * 音声処理周りが重複しているので共通化する
    * GCPだけ動きが少し違うので対策する(空白時間があるのに文が繋がってしまう)
    * (ただの趣味だけど)TornadeからResponderに変えたい(書きやすそうだし)
    * フロントをReactベースにする(見た目重視)
    * Nuanceもやる？: https://developer.nuance.com/public/index.php?task=home

"""

# 標準ライブラリ
import os

# pipで入れたもの
import tornado
from logzero import logger

# 内部module
import controller

BASE_DIR = os.path.dirname(__file__)

app = tornado.web.Application([
    ('/api/recognition', controller.CreateSessionHandler),
    ('/api/recognition/(.*)/start', controller.StartRecognitionHandler),
    ('/api/recognition/(.*)/stop', controller.StopRecognitionHandler),
    ('/api/recognition/(.*)/websocket', controller.WebSocketHandler),
    ('/', tornado.web.RedirectHandler, {'url': '/index.html'}),
    ('/(.*)', tornado.web.StaticFileHandler, {'path': './front/public'}),
])

if __name__ == "__main__":
    app.listen(8000)
    logger.info("Start server.")
    tornado.ioloop.IOLoop.instance().start()
