import threading
import time


class StateManager:

    def __init__(self):
        self._lock = threading.Lock()

        self.user_is_speaking = False
        self.last_time_speech = time.time()
        self.last_ai_speech = time.time()
        self.evil_mode = False  # ← estava faltando

    # -------------------------
    # EVIL MODE
    # -------------------------

    def set_evil_mode(self, value: bool):
        with self._lock:
            self.evil_mode = value

    def is_evil_mode(self):
        with self._lock:
            return self.evil_mode

    # -------------------------
    # USER SPEAKING
    # -------------------------

    def set_user_speaking(self, value: bool):
        with self._lock:
            self.user_is_speaking = value

    def is_user_speaking(self):
        with self._lock:
            return self.user_is_speaking

    # -------------------------
    # SPEECH TIME
    # -------------------------

    def update_last_speech(self):
        with self._lock:
            self.last_time_speech = time.time()

    def get_last_speech(self):
        with self._lock:
            return self.last_time_speech

    def update_last_ai_speech(self):
        with self._lock:
            self.last_ai_speech = time.time()

    def get_last_ai_speech(self):
        with self._lock:
            return self.last_ai_speech
