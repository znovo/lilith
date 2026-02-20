import pyautogui
import threading
import time
import base64

class VisionSystem:
    def __init__(self, output_file="lilith_vision.png", width=720, height=480, interval=20):
        self.output_file = output_file
        self.width = width
        self.height = height
        self.interval = interval
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def capture_screenshot(self):
        """
        Captura a tela, redimensiona e salva no arquivo configurado.
        """
        with self._lock:
            screenshot = pyautogui.screenshot()
            screenshot = screenshot.resize((self.width, self.height))
            screenshot.save(self.output_file)
            return self.output_file

    def encode(self, image_path=None):
        """
        Converte a imagem em base64 para enviar pela API.
        """
        path = image_path or self.output_file
        with self._lock:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")

    def _capture_loop(self):
        """
        Loop interno que captura a tela a cada ´interval´ segundos.
        """
        while self._running:
            self.capture_screenshot()
            time.sleep(self.interval)

    def start_loop(self):
        """
        Inicia a thread de captura de tela contínua (daemon).
        """
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()

    def stop_loop(self):
        """
        Para a thread de captura.
        """
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None
