from events.event_types import EyeEvent

class IntentionEngine:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Centro de la mirada (intentar cargar desde config)
        self.center_x = self.config_manager.get("center_x", 0.5)
        self.center_y = self.config_manager.get("center_y", 0.5)
        
        # Umbrales direccionales (intentar cargar desde config, sino usar default)
        default_x = self.config_manager.get("threshold_x", 0.02)
        default_y = self.config_manager.get("threshold_y", 0.02)
        
        self.threshold_left = self.config_manager.get("threshold_left", default_x)
        self.threshold_right = self.config_manager.get("threshold_right", default_x)
        self.threshold_up = self.config_manager.get("threshold_up", default_y)
        self.threshold_down = self.config_manager.get("threshold_down", default_y)
        
        self.calibration_points = {}

    def record_calibration_point(self, target, rel_x, rel_y):
        self.calibration_points[target] = (rel_x, rel_y)
        if target == EyeEvent.GAZE_CENTER:
            self.center_x = rel_x
            self.center_y = rel_y
        print(f"[IntentionEngine] Grabado {target.value}: X={rel_x:.3f}, Y={rel_y:.3f}")

    def finish_calibration(self):
        if EyeEvent.GAZE_CENTER not in self.calibration_points:
            return

        cx, cy = self.calibration_points[EyeEvent.GAZE_CENTER]
        
        # Calcular umbrales asimétricos
        if EyeEvent.GAZE_LEFT in self.calibration_points:
            lx, _ = self.calibration_points[EyeEvent.GAZE_LEFT]
            self.threshold_left = abs(lx - cx) * 0.6
            
        if EyeEvent.GAZE_RIGHT in self.calibration_points:
            rx, _ = self.calibration_points[EyeEvent.GAZE_RIGHT]
            self.threshold_right = abs(rx - cx) * 0.6
            
        if EyeEvent.GAZE_UP in self.calibration_points:
            _, uy = self.calibration_points[EyeEvent.GAZE_UP]
            self.threshold_up = abs(uy - cy) * 0.6
            
        if EyeEvent.GAZE_DOWN in self.calibration_points:
            _, dy = self.calibration_points[EyeEvent.GAZE_DOWN]
            self.threshold_down = abs(dy - cy) * 0.6

        # Protección contra umbrales cero o ruidosos
        min_t = 0.005
        self.threshold_left = max(self.threshold_left, min_t)
        self.threshold_right = max(self.threshold_right, min_t)
        self.threshold_up = max(self.threshold_up, min_t)
        self.threshold_down = max(self.threshold_down, min_t)
            
        print(f"[IntentionEngine] Calibración asimétrica -> L:{self.threshold_left:.4f} R:{self.threshold_right:.4f} U:{self.threshold_up:.4f} D:{self.threshold_down:.4f}")

        # Guardar calibración en config
        self.config_manager.set("center_x", cx)
        self.config_manager.set("center_y", cy)
        self.config_manager.set("threshold_left", self.threshold_left)
        self.config_manager.set("threshold_right", self.threshold_right)
        self.config_manager.set("threshold_up", self.threshold_up)
        self.config_manager.set("threshold_down", self.threshold_down)
        self.config_manager.save_config()
        print("[IntentionEngine] Calibración guardada permanentemente en tracking.json")

    def evaluate_intention(self, rel_x, rel_y):
        """
        Convierte coordenadas relativas del iris en intenciones discretas.
        """
        dx = rel_x - self.center_x
        dy = rel_y - self.center_y

        center_priority = self.config_manager.get("centerpriority", True)
        
        # Usamos los umbrales específicos de la dirección hacia la que mira
        current_threshold_x = self.threshold_left if dx > 0 else self.threshold_right
        current_threshold_y = self.threshold_down if dy > 0 else self.threshold_up

        # Si centerpriority es true, le damos más margen al centro
        deadzone_multiplier_x = 1.2 if center_priority else 1.0
        deadzone_multiplier_y = 1.2 if center_priority else 1.0

        if abs(dx) < (current_threshold_x * deadzone_multiplier_x) and abs(dy) < (current_threshold_y * deadzone_multiplier_y):
            return EyeEvent.GAZE_CENTER

        # Normalizar las diferencias usando los umbrales asimétricos.
        norm_dx = abs(dx) / current_threshold_x
        norm_dy = abs(dy) / current_threshold_y

        # Determinar dirección primaria (eje con mayor desviación relativa)
        if norm_dx > norm_dy:
            # Movimiento horizontal
            if dx > 0:
                return EyeEvent.GAZE_LEFT # Aumenta X
            else:
                return EyeEvent.GAZE_RIGHT
        else:
            # Movimiento vertical
            if dy > 0:
                return EyeEvent.GAZE_DOWN # Aumenta Y
            else:
                return EyeEvent.GAZE_UP

        return EyeEvent.GAZE_CENTER
