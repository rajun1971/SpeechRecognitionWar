# -*- coding: utf-8 -*-

import os
import os.path
import dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
dotenv.load_dotenv(dotenv_path)

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY")
AZURE_SERVICE_REGION = os.environ.get("AZURE_SERVICE_REGION")
WATSON_APIKEY = os.environ.get("WATSON_APIKEY")
WATSON_URL = os.environ.get("WATSON_URL")
RECAIUS_ID = os.environ.get("RECAIUS_ID")
RECAIUS_PASSWORD = os.environ.get("RECAIUS_PASSWORD")
