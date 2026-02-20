import random

class EmotionSystem:

    def __init__(self):
        self.base = {
            "feliz": 0.6,
            "ansiosa": 0.2,
            "curiosa": 0.5,
            "irritada": 0.1,
            "atenta": 0.6,
            "entediada": 0.2,
            "calma": 0.7,
            "neutra": 0.5
        }

        # Estado emocional atual (dinâmico)
        self.estado = self.base.copy()

    # -------------------------
    # Atualização emocional
    # -------------------------

    def update(self, texto):
        texto = texto.lower()

        # Curiosidade aumenta se tiver pergunta
        if "?" in texto or "por que" in texto:
            self.estado["curiosa"] += 0.05

        # Irritação aumenta com palavras negativas
        if any(p in texto for p in ["raiva", "ódio", "burro", "idiota"]):
            self.estado["irritada"] += 0.1
            self.estado["calma"] -= 0.05

        # Felicidade aumenta com palavras positivas
        if any(p in texto for p in ["legal", "bom", "gostei"]):
            self.estado["feliz"] += 0.08
            self.estado["irritada"] -= 0.05

        self._equilibrar()
        self._retornar_ao_neutro(taxa=0.02)

    # -------------------------
    # Equilíbrio entre emoções
    # -------------------------

    def _equilibrar(self):

        if self.estado["irritada"] > 0.5:
            self.estado["feliz"] -= 0.1

        if self.estado["feliz"] > 0.7:
            self.estado["curiosa"] += 0.05

        if self.estado["ansiosa"] > 0.5:
            self.estado["calma"] -= 0.1

        self._normalizar()

    def apply_evil_modifier(self):
        if self.state.is_evil_mode():
            self.estado["irritada"] += 0.05
            self.estado["curiosa"] += 0.03
            self.estado["atenta"] += 0.02


    # -------------------------
    # Retorno gradual ao padrão
    # -------------------------

    def _retornar_ao_neutro(self, taxa=0.01):
        for emocao in self.estado:
            base_valor = self.base[emocao]
            atual = self.estado[emocao]
            self.estado[emocao] += (base_valor - atual) * taxa

    # -------------------------
    # Normalização
    # -------------------------

    def _normalizar(self):
        for chave in self.estado:
            self.estado[chave] = max(0.0, min(1.0, self.estado[chave]))

    # -------------------------
    # Emoção dominante
    # -------------------------

    def emocao_dominante(self):
        return max(self.estado, key=self.estado.get)
