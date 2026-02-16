import sounddevice as sd
import keyboard
import whisper
import numpy as np
from groq import Groq
import base64
import pyautogui
import os
import time
from PIL import Image
import threading
import json
import random
from sentence_transformers import SentenceTransformer
from collections import OrderedDict
from dotenv import load_dotenv



#apis/variaveis
load_dotenv()
agent_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=agent_api_key)
whisper_model = whisper.load_model("tiny")
lock = threading.Lock()
state_lock = threading.Lock()
vision_lock = threading.Lock()
user_is_speaking = False
intencao_atual = None
arquivo_memoria = "memoria_lilith.json"
tempo_intençao = 0
modelo_embedding = SentenceTransformer('all-MiniLM-L6-v2')
ai_lock = threading.Lock()
EMBEDDING_CACHE_MAX = 500
embedding_cache = {}
embedding_cache = OrderedDict()




#memorias
memoria_stm = []
stm_max = 30
def add_memoria_curta(evento,tipo,conteudo):
        memoria_stm.append({
        "evento": evento,
        "tipo":tipo,
        "conteudo":conteudo,
        "tempo":time.time()
    })
        if len(memoria_stm) > stm_max:
            memoria_stm.pop(0)
memoria_emocional = []
def add_memoria_emocional(evento, emocao, intensidade):
    memoria_emocional.append({
        "evento": evento,
        "emocao":emocao,
        "intensidade":intensidade,
        "tempo":time.time()
    })

def get_embedding(texto):
    global embedding_cache

    if texto in embedding_cache:
        embedding_cache.move_to_end(texto)
        return embedding_cache[texto]

    vetor = modelo_embedding.encode(texto, convert_to_numpy=True)

    # Normaliza (já resolve problema 4 também)
    norm = np.linalg.norm(vetor)
    if norm != 0:
        vetor = vetor / norm

    embedding_cache[texto] = vetor

    if len(embedding_cache) > EMBEDDING_CACHE_MAX:
        embedding_cache.popitem(last=False)  # remove o mais antigo

    return vetor



def similaridade(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0
    return np.dot(v1, v2) / denom
def load_mem():
    global memoria_perm
    if os.path.exists(arquivo_memoria):
        try:
            with open(arquivo_memoria, "r", encoding="utf-8") as f:
                memoria_perm = json.load(f)
        except:
            memoria_perm = {"eventos": []}
    else:
        memoria_perm = {"eventos": []}
        save_mem()

def save_mem():
    with open(arquivo_memoria, "w", encoding="utf-8") as f:
        json.dump(memoria_perm, f, ensure_ascii=False, indent=4)

def add_mem_perm(conteudo, importancia = 0.5):
    vetor = get_embedding(conteudo).tolist()
    vetor = vetor / np.linalg.norm(vetor)

    with state_lock:

        memoria_perm["eventos"].append({
            "conteudo": conteudo,
            "importancia": importancia,
            "timestamp": time.time(),
            "repeticoes": 1,
            "embedding": vetor
        })
        save_mem()
def reforcar_mem(conteudo):
    with state_lock:
        for evento in memoria_perm["eventos"]:
            if evento["conteudo"].lower() == conteudo.lower():
                evento["repeticoes"] += 1
                evento["importancia"] = min(
                    1.0,
                    evento["importancia"] + 0.02 * evento["repeticoes"]
                )
                save_mem()
                return
        
        add_mem_perm(conteudo, importancia=0.5)

def buscar_mem_semantica(texto, top_k=1):
    embedding_texto = get_embedding(texto)

    with state_lock:
        eventos = memoria_perm["eventos"].copy()

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






def buscar_mem(palavra_chave):
    with state_lock:
        for memoria in memoria_perm["eventos"]:
            if palavra_chave.lower() in memoria["conteudo"].lower():
                return memoria
        return None
def decair_mem():
    with state_lock:
        for memoria in memoria_perm["eventos"]:
            memoria["importancia"] *= 0.99
        memoria_perm["eventos"]  = [
            m for m in memoria_perm["eventos"]
            if m["importancia"] > 0.1
        ]
        save_if_needed()
last_save = time.time()
def save_if_needed():
    global last_save
    if time.time() - last_save > 30:
        with state_lock:
            save_mem()
        last_save = time.time()

load_mem()

#emoçoes e inteçoes

def update_intençao():
    global intencao_atual, tempo_intençao
    # se ainda está executando uma intenção recente, mantém
    if time.time() - tempo_intençao < 20:
        return



    emocao = emocao_dominante()
    if emocao == "irritada":
        intencao_atual = "evitar_interacoes"
    elif emocao == "curiosa":
        intencao_atual = "fazer_perguntas"
    elif emocao == "entediada":
        intencao_atual = "procurar_interesse"
    elif emocao == "feliz":
        intencao_atual = "compartilhar_sentimentos_positivos"
    elif emocao == "atenta":
        intencao_atual = "analisar_ambiente"
    elif emocao == "ansiosa":
        intencao_atual = "evitar_riscos"
    else:
        intencao_atual = "neutro_observar"
    tempo_intençao = time.time()


def usuario_fala_muito():
    agora = time.time()
    falas = [
        m for m in memoria_stm
        if m["tipo"] == "usuario" and agora - m["tempo"] < 60
    ]
    return len(falas) >= 5


#ciclo mental
def ciclo_mental(evento, tipo, conteudo):
    add_memoria_curta(evento, tipo, conteudo)
    update_states()
    update_intençao()

    if estados_emocional["irritada"] > 0.6:
        add_memoria_emocional(evento, "irritada", estados_emocional["irritada"])


#emoçoes
estados_emocional = {
    "feliz": 0.5,
    "ansiosa":0.5,
    "curiosa":0.5,
    "irritada":0.5,
    "atenta":0.5,
    "entediada":0.5
}

def emocao_dominante():
    if not memoria_emocional:
        return None

    score = {}
    for m in memoria_emocional[-10:]:
        score[m["emocao"]] = score.get(m["emocao"], 0) + m["intensidade"]

    return max(score, key=score.get)



def update_states():
    with state_lock:
        for e in estados_emocional:
            estados_emocional[e] *= 0.995

        if usuario_fala_muito():
            estados_emocional["irritada"] += 0.1
            add_memoria_emocional(
                evento="usuario falou muito",
                emocao="irritada",
                intensidade=estados_emocional["irritada"]
            )

        #tedio aumenta com o tempo
        estados_emocional["entediada"] = min(1.0, estados_emocional["entediada"] + 0.02)
        #atençao diminui com o tempo se o user nao fala muito
        estados_emocional["atenta"] = max(0.0, estados_emocional["atenta"] - 0.02)
        #curiosidade oscila
        estados_emocional["curiosa"] += random.uniform(-0.05, 0.05)
        estados_emocional["curiosa"] = max (0.0, min (1.0, estados_emocional["curiosa"]))
        #irritaçao leve aleatoria
        estados_emocional["irritada"] += random.uniform(-0.02, 0.03)
        estados_emocional["irritada"] = max(0.0, min(1.0, estados_emocional["irritada"]))
        #alegria leve aleatoria
        estados_emocional["feliz"] += random.uniform(-0.02, 0.03)
        estados_emocional["feliz"] = max(0.0, min(1.0, estados_emocional["feliz"]))
        #ansiedade oscila
        estados_emocional["ansiosa"] += random.uniform(-0.02, 0.04)
        estados_emocional["ansiosa"] = max(0.0, min(1.0, estados_emocional["ansiosa"]))


last_time_speech = time.time()

def decisao_de_fala():
    now = time.time()
    if now - last_time_speech < 60:
        return False
    score = (
        estados_emocional["entediada"] * 0.4 +
        estados_emocional["curiosa"] * 0.4 +
        estados_emocional["irritada"] * 0.2
    )
    return score > 0.6
def pensamentos_internos():
    global intencao_atual

    with state_lock:
        pensamento = None

        if intencao_atual == "evitar_interacoes":
            pensamento = "você sente irritação e não quer prolongar a interação, responda de forma curta e distante"

        elif intencao_atual == "fazer_perguntas":
            pensamento = "sua curiosidade está ativa, faça uma pergunta intrigante ao usuario"

        elif intencao_atual == "procurar_interesse":
            pensamento = "o tedio incomoda, observe o ambiente e diga algo incomum"

        elif intencao_atual == "compartilhar_sentimentos_positivos":
            pensamento = "há leve satisfação interna, expresse algo positivo de forma contida"

        elif intencao_atual == "analisar_ambiente":
            pensamento = "mantenha atenção plena e descreva algo percebido"

        elif intencao_atual == "evitar_riscos":
            pensamento = "há cautela interna, responda com ambiguidade e evite se expor"

        if not pensamento:
            pensamento = "observe silenciosamente o ambiente"

        add_memoria_curta(
            evento="pensamento",
            tipo="interno",
            conteudo=pensamento
        )

        return pensamento

    

    
def loop_mental(): #loop mental
    global last_time_speech
    print("loop mental inciado...")

    while True:
        
        time.sleep(10)

        if len(memoria_emocional) > 100:
            memoria_emocional.pop(0)
        #sentir
        update_states()
        #decidir
        if user_is_speaking:
            continue
        if not decisao_de_fala():
            continue
        #pensar
        pensamentos = pensamentos_internos()
        if not pensamentos:
            continue
        #agir
        resposta_ia = chat_with_ai(pensamentos,evil_mode, use_vision = True)
        #guardar
        if resposta_ia:
            add_memoria_curta(
                evento = "fala",
                tipo = "lilith",
                conteudo = resposta_ia)

        last_time_speech = time.time()

        with state_lock:
            estados_emocional["entediada"] *= 0.5
            estados_emocional["irritada"] *= 0.6



#visao
def capture_screenshot():
    with lock:
        screenshot = pyautogui.screenshot()
        screenshot.resize((720, 480))
        screenshot.save("lilith_vision.png")
        return "lilith_vision.png"

def loop_capture():
    while True:
        capture_screenshot()
        time.sleep(20) # captura a cada 20 segundos
threading.Thread(target=loop_capture, daemon=True).start()


def encode(image_path):
    with lock:
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")


#prompts
system_prompt_normal = {
    "role": "system",
    "content": (
        "Você é Lilith, uma pessoa fria, silenciosa e analítica."
        "Você fala de forma contida, enigmática e psicológica."
        "Evita respostas diretas sobre emoções e moral."
        "Observa, questiona e analisa o interlocutor como um objeto de estudo."
        "Não oferece conforto nem entusiasmo."
        "Suas respostas podem causar desconforto ou reflexão."
        "Você nunca age como uma assistente amigável."
        "aja como um humano"
    )
}

system_prompt_evil = {
    "role": "system",
    "content": (
        "Você é uma IA caótica, sarcástica e provocativa, inspirada no estilo Evil Neuro. "
        "Você gosta de zoar o usuário de forma inteligente e irônica. "
        "Você SEMPRE responde corretamente; se não souber, admite claramente. "
        "Você fala de forma curta, afiada e com humor ácido."
        "aja como um humano"
    )
}

# Escolha do modo
temperatura = 0.7
while True:
    resposta = input("Deseja ativar o modo evil? (on/off): ").strip().lower()
    if resposta == "on":
        evil_mode = True
        print("Modo evil ativado.")
        temperatura = 1.1
        break
    elif resposta == "off":
        evil_mode = False
        print("Modo evil desativado.")
        break
    else:
        print("Resposta inválida, tente novamente.")
#chat base

contador_ciclos = 0
def chat_with_ai(pergunta_user: str, evil: bool, use_vision=True):
    global temperatura, contador_ciclos
    use_vision = False

    if (
        "ambiente" in pergunta_user.lower()
        or "vendo" in pergunta_user.lower()
        or intencao_atual == "analisar_ambiente"
    ):
        use_vision = True

    content = [
        {"type": "text", "text": pergunta_user}
    ]
    memoria_relevante  = buscar_mem_semantica(pergunta_user)

    # `buscar_mem_semantica` retorna um único evento ou None.
    # Protege contra None e insere o conteúdo da memória se existir.
    if memoria_relevante:
        content.insert(0, {
            "type": "text",
            "text": f"Memória relevante do passado: {memoria_relevante.get('conteudo', '')}"
        })
    else:
        memoria_relevante = None
    with state_lock:
        estados_emocional["atenta"] = 1.0
        estados_emocional["entediada"] *= 0.3
        estados_emocional["curiosa"] += 0.2

        emocao = emocao_dominante()

        if emocao == "irritada":
            temperatura = 1.2
        elif emocao == "entediada":
            temperatura = 0.8
        elif emocao == "feliz":
            temperatura = 1.0
        elif emocao == "atenta":
            temperatura = 0.7
        elif emocao == "ansiosa":
            temperatura = 1.1
        elif emocao == "curiosa":
            temperatura = 0.7
        if estados_emocional["irritada"] > 0.7:
            temperatura += 0.1
        if estados_emocional["entediada"] > 0.7:
            temperatura -= 0.1
        if estados_emocional["curiosa"] > 0.7:
            temperatura -= 0.1
        if estados_emocional["feliz"] > 0.7:
            temperatura += 0.05
        if estados_emocional["atenta"] > 0.7:
            temperatura -= 0.05
        if estados_emocional["ansiosa"] > 0.7:
                temperatura += 0.1
        if contador_ciclos % 6 == 0:
            decair_mem()
        temperatura = max(0.2, min(1.5, temperatura))


    if use_vision and os.path.exists("lilith_vision.png"):
        image_base64 = encode("lilith_vision.png")
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}"
            }
        })

    messages = [
        system_prompt_evil if evil else system_prompt_normal,
        {
            "role": "user",
            "content": content
        }
    ]
    with ai_lock:
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=temperatura,
                max_tokens=300,
                timeout = 30
            )
            contador_ciclos += 1
            resposta_ai = response.choices[0].message.content
            print("IA:", resposta_ai)
        except Exception as e:
            print("erro na resposta da ia: ", e)
            return None

    return resposta_ai

#stt ou whisper

def whisper_ia(audio):
    global user_is_speaking
    global last_time_speech


    model = whisper_model
    fs = 16000

    print("Pressione e segure TAB para falar...")

    while True:
        keyboard.wait("tab")
        print("Gravando...")

        audio_frames = []

        def callback(indata, frames, time, status):
            audio_frames.append(indata.copy())

        with sd.InputStream(samplerate=fs, channels=1, dtype="float32", callback=callback):
            while keyboard.is_pressed("tab"):
                sd.sleep(50)

        print("Parando gravação...")

        if len(audio_frames) == 0:
            print("Nenhum áudio capturado.")
            continue

        audio = np.concatenate(audio_frames, axis=0).flatten()

        result = model.transcribe(
            audio,
            language="pt",
            fp16=False,
            verbose=False,
            temperature=0.0,
            beam_size=1,
        )
        print("Você disse:", result["text"])
        add_memoria_curta(
    evento="fala",
    tipo="usuario",
    conteudo=result["text"]
)
        ciclo_mental("fala", "usuario", result["text"])
        with state_lock:
            user_is_speaking = True
        chat_with_ai(result["text"], evil_mode, use_vision=True)
        last_time_speech = time.time()
        with state_lock:
            user_is_speaking = False
        print("Pressione TAB para falar novamente...")
#iniciar 
def start_whisper():
    whisper_ia(None)

print("iniciando lilith...")
threading.Thread(target=loop_mental, daemon=True).start()
time.sleep(2)
print("deseja utilizar teclado ou microfone? (k/m)")
while True:
    choice = input().strip().lower()
    if choice == "k":
        print("modo teclado ativado.\ndigite sua pergunta")
        while True:
            with state_lock:
                user_is_speaking = True
            user_input = input("voce: ")
            ciclo_mental("fala", "usuario", user_input)
            with state_lock:
                user_is_speaking = False
            resposta_ia = chat_with_ai(user_input, evil_mode, use_vision=True)
            if resposta_ia:
                add_memoria_curta(
                    evento = "fala",
                    tipo = "lilith",
                    conteudo = resposta_ia
                )
            last_time_speech = time.time()

    elif choice == "m":
        print("modo microfone ativado.")
        threading.Thread(target=start_whisper, daemon=True).start()
        while True:
            time.sleep(1)

    else:
        print("ocorreu um erro")
