# -*- coding: utf-8 -*-
import time
import threading
from typing import Dict


class SessionCollector:
    _instance = None
    _lock = threading.Lock()
    _sessions: Dict[str, dict] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def CreateSession(self):
        session_id = str(time.time())
        self._sessions[session_id] = {}
        return session_id

    def SetPropertyInSession(self, session_id, value):
        if(session_id in self._sessions):
            self._sessions[session_id].update(value)
            return True
        else:
            return False

    def GetPropertyInSession(self, session_id):
        return self._sessions[session_id]

    def DeleteSession(self, session_id):
        self._sessions.pop(session_id)
