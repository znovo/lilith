import time
import random


class MentalLoop:

    def __init__(self, emotion_system, intention_system, memory_system,
                 conversation_system, state_manager):

        self.emotion = emotion_system
        self.intention = intention_system
        self.memory = memory_system
        self.conversation = conversation_system
        self.state = state_manager

        self.running = False

    def start(self):
        self.running = True
        import threading
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):

        while self.running:

            if self.state.is_user_speaking():
                time.sleep(0.5)
                continue

            # Evil influencia emoção continuamente
            if self.state.is_evil_mode():
                self.emotion.apply_evil_modifier()

            self.emotion.passive_decay()
            self.intention.update()
            self.memory.consolidate()

            self._maybe_initiate_conversation()

            time.sleep(1)

    # ------------------------------------
    # PROATIVIDADE
    # ------------------------------------

    def _maybe_initiate_conversation(self):

        if self.state.is_evil_mode():
            silence_threshold = 15
            cooldown = 30
        else:
            silence_threshold = 30
            cooldown = 60

        silence_time = time.time() - self.state.get_last_speech()
        ai_silence = time.time() - self.state.get_last_ai_speech()

        if silence_time < silence_threshold:
            return

        if ai_silence < cooldown:
            return

        curiosity = self.emotion.get_emotion("curiosa")
        boredom = self.emotion.get_emotion("entediada")

        chance = 0

        if curiosity > 0.6:
            chance += 0.4

        if boredom > 0.7:
            chance += 0.3

        # Evil aumenta chance de falar
        if self.state.is_evil_mode():
            chance += 0.2

        if random.random() < chance:
            self._start_conversation()

    # ------------------------------------

    def _start_conversation(self):

        prompt = self.conversation.build_proactive_prompt()

        response = self.conversation.generate_response(prompt)

        print(f"Lilith: {response}")

        self.state.update_last_ai_speech()
    