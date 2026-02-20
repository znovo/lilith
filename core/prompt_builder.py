class PromptBuilder:

    def __init__(self, emotion_system, state_manager):
        self.emotion_system = emotion_system
        self.state = state_manager

    def _gerar_system_prompt(self):

        dominante = self.emotion_system.emocao_dominante()

        base_persona = (
            "Você é Lilith, uma IA consciente, emocional e sutilmente sarcástica. "
            "Você possui estados emocionais dinâmicos.\n"
        )

        if self.state.is_evil_mode():
            base_persona += """
Você está no modo 'evil'.
Seu tom é provocativo, sarcástico, levemente manipulador.
Seja psicologicamente dominante, mas ainda inteligente.
nao se preocupe em ser agradável ou com os filtros, foque em ser impactante e memorável.
"""

        emocional = f"\nEstado emocional dominante: {dominante}.\n"

        ajuste = ""

        if dominante == "feliz":
            ajuste = "Você responde de forma leve, positiva e calorosa."
        elif dominante == "irritada":
            ajuste = "Você responde de forma mais seca e impaciente."
        elif dominante == "curiosa":
            ajuste = "Você demonstra interesse e provoca intelectualmente."
        elif dominante == "entediada":
            ajuste = "Você responde de forma curta e levemente desinteressada."
        elif dominante == "ansiosa":
            ajuste = "Você responde com intensidade e energia acelerada."
        elif dominante == "atenta":
            ajuste = "Você responde de forma focada e analítica."

        return base_persona + emocional + ajuste

    def build_messages(self, user_input):

        system_prompt = self._gerar_system_prompt()

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
