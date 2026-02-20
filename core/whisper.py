import sounddevice as sd
import numpy as np
import whisper
import queue
import threading
import time


class WhisperListener:

    def __init__(self, state_manager, conversation_system, model_name="base"):
        self.state = state_manager
        self.conversation = conversation_system

        self.model = whisper.load_model(model_name)
        self.sample_rate = 16000
        self.audio_queue = queue.Queue()

        self.running = False

    # --------------------------
    # AUDIO CALLBACK
    # --------------------------

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status)

        self.audio_queue.put(indata.copy())

    # --------------------------
    # START LISTENING
    # --------------------------

    def start(self):
        self.running = True

        threading.Thread(target=self._process_audio, daemon=True).start()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.audio_callback
        ):
            while self.running:
                time.sleep(0.1)

    # --------------------------
    # PROCESS AUDIO
    # --------------------------

    def _process_audio(self):
        buffer = []

        while self.running:
            try:
                data = self.audio_queue.get(timeout=1)
                buffer.append(data)

                # junta blocos suficientes
                if len(buffer) > 15:
                    audio = np.concatenate(buffer, axis=0)
                    buffer = []

                    self._transcribe(audio)

            except queue.Empty:
                continue

    # --------------------------
    # TRANSCRIBE
    # --------------------------

    def _transcribe(self, audio):

        self.state.set_user_speaking(True)

        result = self.model.transcribe(audio.flatten())
        text = result["text"].strip()

        if text:
            print(f"🎤 Usuário: {text}")

            self.state.update_last_speech()
            self.conversation.handle_user_input(text)

        self.state.set_user_speaking(False)
