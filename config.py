import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import whisper


load_dotenv()

agent_api_key = os.getenv("GROQ_API_KEY")
model_chat = "meta-llama/llama-4-scout-17b-16e-instruct"
whisper_model = whisper.load_model("tiny")
arquivo_memoria = "memoria_lilith.json"
modelo_embedding = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_CACHE_MAX = 500
stm_max = 30