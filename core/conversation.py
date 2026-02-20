import requests
import os
from config import model_chat
from config import agent_api_key
import threading
from core.emotion import EmotionSystem
from groq import Groq
from core.memory import MemoryManager
from core.intention import IntentionSystem


class ConversationSystem:

    def __init__(self, emotion, memory, intention):
        self.emotion = emotion
        self.memory = memory
        self.intention = intention
        self.client = Groq(api_key=agent_api_key)
        self.temperature = 0.7
        self.ai_lock = threading.Lock()
        self.contador_ciclos = 0
    def process(self, user_input):

        # 1️⃣ Atualiza emoção
        self.emotion.update(user_input)

        # 2️⃣ Atualiza intenção
        self.intention.update(self.emotion.estado)

        # 3️⃣ Recupera memória
        memoria_relevante = self.memory.buscar_mem_semantica(user_input)


        # 4️⃣ Constrói mensagens base
        messages = self.prompt_builder.build_messages(
            user_input=user_input,
            memoria=memoria_relevante,
            intencao=self.intention.obter()
        )

        # 5️⃣ Adiciona visão se existir
        if self.vision:
            image_b64 = self.vision.encode()
            if image_b64:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analise a imagem atual da tela."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                })

        temperature = self._ajustar_temperatura()

        payload = {
            "model": model_chat,
            "messages": messages,
            "temperature": temperature
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.url, headers=headers, json=payload)

        if response.status_code != 200:
            print("Erro Groq:", response.text)
            return "Erro ao gerar resposta."

        data = response.json()
        resposta_texto = data["choices"][0]["message"]["content"]

        # 6️⃣ Armazena memória
        self.memory.add_memoria_curta("usuario", "entrada", user_input)
        self.memory.add_memoria_curta("ia", "resposta", resposta_texto)
        self.memory.add_mem_perm(resposta_texto, importancia=0.4)


        return resposta_texto

    def _ajustar_temperatura(self):

        dominante = self.emotion.emocao_dominante()

        mapa = {
            "feliz": 0.9,
            "curiosa": 0.85,
            "ansiosa": 0.8,
            "irritada": 0.6,
            "atenta": 0.5,
            "entediada": 0.4
        }

        return mapa.get(dominante, 0.7)
