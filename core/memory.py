import os
import json
import time
import numpy as np
from collections import OrderedDict
import threading
from core.embendding_cache import EmbeddingCache


class MemoryManager:

    def __init__(self, modelo_embedding, memory_file, stm_max):
        self.modelo_embedding = modelo_embedding
        self.memory_file = memory_file
        self.stm_max = stm_max

        self.memoria_stm = []
        self.memoria_perm = {"eventos": []}
        self.memoria_emocional = []

        self.embedding_cache = OrderedDict()
        self.lock = threading.Lock()

        self.load_mem()

    # -------------------------
    # MEMÓRIA CURTA
    # -------------------------

    def add_memoria_curta(self, evento, tipo, conteudo):
        self.memoria_stm.append({
            "evento": evento,
            "tipo": tipo,
            "conteudo": conteudo,
            "tempo": time.time()
        })

        if len(self.memoria_stm) > self.stm_max:
            self.memoria_stm.pop(0)

    # -------------------------
    # MEMÓRIA EMOCIONAL
    # -------------------------

    def add_memoria_emocional(self, evento, emocao, intensidade):
        self.memoria_emocional.append({
            "evento": evento,
            "emocao": emocao,
            "intensidade": intensidade,
            "tempo": time.time()
        })

    # -------------------------
    # EMBEDDING
    # -------------------------

    def get_embedding(self, texto):
        cached = self.embedding_cache.get(texto)
        if cached is not None:
            return cached
        self.embedding_cache.add(texto, vetor)
        if texto in self.embedding_cache:
            self.embedding_cache.move_to_end(texto)
            return self.embedding_cache[texto]

        vetor = self.modelo_embedding.encode(texto, convert_to_numpy=True)

        norm = np.linalg.norm(vetor)
        if norm != 0:
            vetor = vetor / norm

        self.embedding_cache[texto] = vetor

        if len(self.embedding_cache) > 500:
            self.embedding_cache.popitem(last=False)

        return vetor

    # -------------------------
    # MEMÓRIA PERMANENTE
    # -------------------------

    def load_mem(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memoria_perm = json.load(f)
            except:
                self.memoria_perm = {"eventos": []}
        else:
            self.memoria_perm = {"eventos": []}
            self.save_mem()

    def save_mem(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memoria_perm, f, ensure_ascii=False, indent=4)

    def add_mem_perm(self, conteudo, importancia=0.5):

        vetor = self.get_embedding(conteudo).tolist()

        with self.lock:
            self.memoria_perm["eventos"].append({
                "conteudo": conteudo,
                "importancia": importancia,
                "timestamp": time.time(),
                "repeticoes": 1,
                "embedding": vetor
            })

            self.save_mem()

    def reforcar_mem(self, conteudo):

        with self.lock:
            for evento in self.memoria_perm["eventos"]:
                if evento["conteudo"].lower() == conteudo.lower():
                    evento["repeticoes"] += 1
                    evento["importancia"] = min(
                        1.0,
                        evento["importancia"] + 0.02 * evento["repeticoes"]
                    )
                    self.save_mem()
                    return

        self.add_mem_perm(conteudo, importancia=0.5)

    def buscar_mem_semantica(self, texto, top_k=1):

        embedding_texto = self.get_embedding(texto)

        with self.lock:
            eventos = self.memoria_perm["eventos"].copy()

        if not eventos:
            return None

        melhores = []

        for evento in eventos:
            evento_embedding = np.array(evento["embedding"])
            score = np.dot(embedding_texto, evento_embedding)
            melhores.append((score, evento))

        melhores.sort(key=lambda x: x[0], reverse=True)

        if melhores and melhores[0][0] > 0.5:
            return melhores[0][1]

        return None

    def decair_mem(self):
        with self.lock:
            for memoria in self.memoria_perm["eventos"]:
                memoria["importancia"] *= 0.99

            self.memoria_perm["eventos"] = [
                m for m in self.memoria_perm["eventos"]
                if m["importancia"] > 0.1
            ]

            self.save_mem()
