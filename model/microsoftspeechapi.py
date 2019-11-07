# -*- coding: utf-8 -*-
"""
https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/samples/python/console
"""
import threading
import queue

import azure.cognitiveservices.speech as speechsdk
import numpy as np
from logzero import logger

import model.key


def TranscodeFromFile(path, sample_rate):
    speech_key = model.key.AZURE_SPEECH_KEY
    service_region = model.key.AZURE_SERVICE_REGION
    audio_config = speechsdk.audio.AudioConfig(filename=path)
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key,
        region=service_region,
        speech_recognition_language="ja-JP")
    # Creates a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config)
    # Starts speech recognition, and returns after a single utterance is
    #  recognized. The end of a single utterance is determined by listening
    #  for silence at the end or until a maximum of 15 seconds of audio is
    #  processed.  The task returns the recognition text as result.
    # Note: Since recognize_once() returns only a single utterance, it is
    #  suitable only for single shot recognition like command or query.
    # For long-running multi-utterance recognition, use
    #  start_continuous_recognition() instead.
    result = speech_recognizer.recognize_once()
    # Checks result.
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        logger.debug(f"Recognized: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        logger.debug(
            f"No speech could be recognized: {result.no_match_details}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        logger.debug(
            f"Speech Recognition canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            logger.debug(
                f"Error details: {cancellation_details.error_details}")
    return ""


class Transcoder:
    def __init__(self):
        logger.info('__init__:Enter')
        self._token = None
        self.transcript = None
        self._queue = queue.Queue()

    def start(self, token):
        """Start up streaming speech call"""
        logger.info('start:Enter')
        self._token = token
        threading.Thread(target=self.process).start()

    def write_stream(self, buf):
        self._queue.put(buf)

    def process(self):
        logger.info('process:Enter')
        speech_key = model.key.AZURE_SPEECH_KEY
        service_region = model.key.AZURE_SERVICE_REGION
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=service_region,
            speech_recognition_language="ja-JP")
        # setup the audio stream
        stream = speechsdk.audio.PushAudioInputStream(
            stream_format=speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000,
                bits_per_sample=16)
        )
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        # instantiate the speech recognizer with push stream input
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config)

        # Connect callbacks to the events fired by the speech recognizer
        def write_transcribed_data(evt):
            logger.debug(f'write_transcribed(text={evt.result.text})')
            self.transcript = evt.result.text
        speech_recognizer.recognizing.connect(write_transcribed_data)
        speech_recognizer.recognized.connect(write_transcribed_data)
        speech_recognizer.session_started.connect(
            lambda evt: logger.debug('SESSION STARTED: {}'.format(evt)))
        speech_recognizer.session_stopped.connect(
            lambda evt: logger.debug('SESSION STOPPED {}'.format(evt)))
        speech_recognizer.canceled.connect(
            lambda evt: logger.debug('CANCELED {}'.format(evt)))
        # start continuous speech recognition
        logger.info('start transcode')
        speech_recognizer.start_continuous_recognition()
        self.stream_generator(stream)
        speech_recognizer.stop_continuous_recognition()
        stream.close()
        logger.info('end transcode')

    def stream_generator(self, stream):
        logger.info('stream_generator:Enter')
        while True:
            v = self._queue.get()
            if v is None:
                break
            arr = v.astype(np.int16)
            arr_bytes = arr.tobytes('C')
            stream.write(arr_bytes)
