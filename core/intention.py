import time

class IntentionSystem:

    def __init__(self):
        self.intencao_atual = "neutra"
        self.tempo_intencao = time.time()

    def update(self, estado_emocional):

        dominante = max(estado_emocional, key=estado_emocional.get)

        nova_intencao = self._mapear_emocao_para_intencao(dominante)
        tempo_passado = time.time() - self.tempo_intencao
        if nova_intencao != self.intencao_atual and tempo_passado > 5:
            self.intencao_atual = nova_intencao
            self.tempo_intencao = time.time()

    def _mapear_emocao_para_intencao(self, emocao):

        mapa = {
            "curiosa": "explorar",
            "feliz": "engajar",
            "irritada": "responder_direto",
            "ansiosa": "antecipar",
            "entediada": "encerrar",
            "atenta": "analisar"
        }

        return mapa.get(emocao, "neutra")

    def obter(self):
        return self.intencao_atual
