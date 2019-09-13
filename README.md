# SpeechRecognitionWar
A web service that compares various speech recognition engines simultaneously

## What is this?

各社のSpeech to Textエンジンを同時に実行して認識結果を比較することが出来るサービスです。

## Environment
* 実行するPC、またはクラウドサービス上にPython3がインストールされていること
* 各種STTクラウドサービス(GCP,Azure,AWS,Watson)の利用設定が完了していること

## How to build & run

### ローカルで実行する場合

1. gitからクローン
1. cd クローン先のディレクトリ
1. 'python -venv venv'でvirtual env作成
1. 'pip install < requirements.txt'を実行
1. GCPを利用する場合は、実行環境の環境変数にGOOGLE_APPLICATION_CREDENTIALSを設定する
1. Azureを利用する場合は、.env.sampleをリネームし、AZURE_SPEECH_KEYとAZURE_SERVICE_REGIONを設定する(同名の環境変数を設定するでも良い)
1. 'front'ディレクトリにて'npm install && npm run build'実行
1. 'python main.py'で実行
1. ブラウザから'http://localhost:8000'にアクセス
