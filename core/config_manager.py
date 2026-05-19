import json
import os

class ConfigManager:
    def __init__(self, config_path="config/tracking.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            print(f"[ConfigManager] Configuración cargada desde {self.config_path}")
        except FileNotFoundError:
            print(f"[ConfigManager] Error: No se encontró el archivo de configuración en {self.config_path}. Usando valores por defecto.")
            self.config = {
                "directional": True,
                "zones": 5,
                "holdframes": 4,
                "transitiondelay": 120,
                "centerpriority": True,
                "recenter": True,
                "confidencefilter": 0.75,
                "statestability": 0.8,
                "camera_index": 0,
                "threshold_x": 0.02,
                "threshold_y": 0.02
            }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"[ConfigManager] Configuración guardada en {self.config_path}")
        except Exception as e:
            print(f"[ConfigManager] Error al guardar configuración: {e}")

config_manager = ConfigManager()
