from config import *
from core.emotion import EmotionSystem
from core.memory import MemoryManager
from core.emotion import EmotionSystem
from core.intention import IntentionSystem
from core.prompt_builder import PromptBuilder
from core.vision import VisionSystem
from utils.state_manager import StateManager
from core.conversation import ConversationSystem
from core.mental_loop import MentalLoop
from core.whisper import WhisperListener

emotion = EmotionSystem()
memory = MemoryManager(modelo_embedding, arquivo_memoria, stm_max)
intention = IntentionSystem()
vision = VisionSystem(interval= 20)
state = StateManager()
conversation = ConversationSystem(emotion, intention, memory, state)

mental_loop = MentalLoop(emotion, intention, memory, state)
whisper = WhisperListener(state, conversation)

mental_loop.start()

whisper.start()




