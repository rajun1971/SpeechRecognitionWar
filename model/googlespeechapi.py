# -*- coding: utf-8 -*-
"""Transcoder with Google speech API.

https://cloud.google.com/speech-to-text/docs/?hl=ja
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_streaming.py
https://googleapis.github.io/google-cloud-python/latest/speech/index.html
https://github.com/sayonari/GoogleSpeechAPI_stream/blob/master/GoogleSpeechAPI_stream.py
"""

import io
import json
import threading
import queue

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from google.oauth2 import service_account

from logzero import logger
import numpy as np

import model.key


def transcode_from_file(path, sample_rate):
    """Transcode from file function."""
    # Instantiates a client
    client = speech.SpeechClient()
    # Loads the audio into memory
    with io.open(path, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code='ja-JP')
    # Detects speech in the audio file
    response = client.recognize(config, audio)
    try:
        logger.debug(
            f'Transcript: {response.results[0].alternatives[0].transcript}')
        return response.results[0].alternatives[0].transcript
    except Exception as e:
        logger.warning(f'Caught exception:{e}')
        return ""


class Transcoder:
    """Transcoder Class."""

    def __init__(self):
        """Constructor."""
        logger.info('__init__:Enter')
        self.transcript = None
        self.is_final = False
        self._token = None
        self._queue = queue.Queue()
        self._sampling_rate = 16000

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
        account_key = model.key.GOOGLE_SERVICE_ACCOUNT_KEY
        if account_key is None:
            client = speech.SpeechClient()
        else:
            service_account_info = json.loads(account_key)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info)
            client = speech.SpeechClient(credentials=credentials)
        config = speech.types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code='ja-JP',
            sample_rate_hertz=self._sampling_rate,
            enable_automatic_punctuation=True
        )
        streaming_config = types.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
            single_utterance=False
        )
        audio_generator = self._stream_generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        logger.info('Start transcode')
        responses = client.streaming_recognize(streaming_config, requests)
        try:
            self._response_loop(responses)
        except Exception as e:
            logger.warning(f'Caught exception:{e}')
            self.start(self._token)
        logger.info('End transcode')

    def _response_loop(self, responses):
        # Pick up the final result of Speech to text conversion
        logger.info('_response_loop:Enter')
        for response in responses:
            if not response.results:
                logger.debug('not result')
                continue
            result = response.results[0]
            if not result.alternatives:
                logger.debug('not result altanative')
                continue
            transcript = result.alternatives[0].transcript
            self.transcript = transcript
            self.is_final = result.is_final
            if result.is_final:
                logger.debug('gcp_result:' + transcript)
            else:
                logger.debug('gcp_result(temp):' + transcript)

    def _stream_generator(self):
        logger.info('_stream_generator:Enter')
        while True:
            v = self._queue.get()
            if v is None:
                break
            arr = v.astype(np.int16)
            arr_bytes = arr.tobytes('C')
            yield arr_bytes
