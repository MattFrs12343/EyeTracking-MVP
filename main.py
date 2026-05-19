import cv2
import threading
import asyncio
import os
import webbrowser
import tkinter as tk
from core.config_manager import config_manager
from vision.face_mesh import FaceMeshDetector
from tracking.iris_tracker import IrisTracker
from gaze.intention_engine import IntentionEngine
from filters.stability import StabilityFilter
from sockets.server import EventServer
from events.event_types import EyeEvent

def get_monitors():
    import ctypes
    monitors = []
    cb = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_int), ctypes.c_double)(
        lambda hMonitor, hdcMonitor, lprcMonitor, dwData: monitors.append(
            (lprcMonitor[0], lprcMonitor[1], lprcMonitor[2] - lprcMonitor[0], lprcMonitor[3] - lprcMonitor[1])
        ) or 1
    )
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, cb, 0)
    return monitors

class CalibrationOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.w}x{self.h}+0+0")
        
        # Fondo transparente
        self.root.config(bg='black')
        self.root.wm_attributes('-transparentcolor', 'black')
        
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.current_target = None
        self.set_monitor(0)

    def set_monitor(self, index):
        monitors = get_monitors()
        if not monitors:
            return
        if index >= len(monitors):
            index = 0
            
        x, y, w, h = monitors[index]
        self.w = w
        self.h = h
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        # Forzar un redibujado con las nuevas dimensiones
        old_target = self.current_target
        self.current_target = None
        if old_target is not None:
            self.draw_target(old_target)
        self.root.update()

    def draw_target(self, target):
        if self.current_target == target:
            self.root.update()
            return
            
        self.canvas.delete("all")
        self.current_target = target
        if target:
            r = 35
            margin = 100 # Margen simétrico en píxeles
            if target == EyeEvent.GAZE_UP:
                x, y = self.w // 2, margin
            elif target == EyeEvent.GAZE_DOWN:
                x, y = self.w // 2, self.h - margin
            elif target == EyeEvent.GAZE_LEFT:
                x, y = margin, self.h // 2
            elif target == EyeEvent.GAZE_RIGHT:
                x, y = self.w - margin, self.h // 2
            elif target == EyeEvent.GAZE_CENTER:
                x, y = self.w // 2, self.h // 2
                
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='yellow', outline='red', width=3)
        self.root.update()

    def hide(self):
        if self.current_target is not None:
            self.canvas.delete("all")
            self.current_target = None
        self.root.update()
        
    def close(self):
        self.root.destroy()

def main():
    print("[Main] Inicializando sistema de Eye Tracking...")
    face_detector = FaceMeshDetector()
    iris_tracker = IrisTracker()
    intention_engine = IntentionEngine(config_manager)
    stability_filter = StabilityFilter(config_manager)
    
    import json
    command_queue = []

    def ws_callback(message):
        try:
            data = json.loads(message)
            if "command" in data:
                command_queue.append(data)
        except Exception as e:
            print(f"[Main] Error parsing ws message: {e}")

    event_server = EventServer(message_callback=ws_callback)
    server_thread = threading.Thread(target=event_server.run_in_background, daemon=True)
    server_thread.start()

    # Abrir el frontend automáticamente en el navegador por defecto
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend', 'index.html'))
    if os.path.exists(frontend_path):
        print(f"[Main] Abriendo interfaz gráfica: {frontend_path}")
        webbrowser.open(f"file:///{frontend_path}")
    else:
        print("[Main] Advertencia: No se encontró el archivo del frontend.")

    # Lanzar automáticamente el controlador de mouse como proceso en segundo plano
    try:
        mouse_client_path = os.path.join(os.path.dirname(__file__), 'clients', 'mouse_controller.py')
        import subprocess
        subprocess.Popen(["python", mouse_client_path], shell=False)
        print("[Main] Controlador de Mouse iniciado en segundo plano.")
    except Exception as e:
        print(f"[Main] Error al iniciar el controlador de mouse: {e}")

    cam_index = config_manager.get("camera_index", 0)
    print(f"[Main] Intentando conectar a la cámara con índice: {cam_index}")
    cap = cv2.VideoCapture(cam_index)
    
    print("[Main] Presiona 'q' para salir.")
    
    overlay = CalibrationOverlay()

    # Secuencia de calibración
    calibration_sequence = [
        EyeEvent.GAZE_UP,
        EyeEvent.GAZE_CENTER,
        EyeEvent.GAZE_LEFT,
        EyeEvent.GAZE_RIGHT,
        EyeEvent.GAZE_DOWN
    ]
    calib_idx = 0
    in_calibration = True

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        h, w, _ = image.shape
        results = face_detector.process(image)
        
        current_event = None

        if getattr(results, "face_landmarks", None) and len(results.face_landmarks) > 0:
            class FakeLandmarks:
                def __init__(self, landmarks):
                    self.landmark = landmarks
            
            face_landmarks_data = FakeLandmarks(results.face_landmarks[0])
            image = face_detector.draw_landmarks(image, results)
            rel_x, rel_y = iris_tracker.calculate_relative_iris_position(face_landmarks_data, w, h)
            
            key = cv2.waitKey(1) & 0xFF

            # Procesar comandos web
            while command_queue:
                data = command_queue.pop(0)
                cmd = data.get("command", "")
                if cmd == "RECALIBRATE":
                    calib_idx = 0
                    in_calibration = True
                    intention_engine.calibration_points.clear()
                    print("[Main] Reiniciando calibración desde la web...")
                elif cmd == "SET_MONITOR":
                    mon_idx = data.get("index", 0)
                    overlay.set_monitor(mon_idx)
                    print(f"[Main] Monitor seleccionado para calibración: Pantalla {mon_idx + 1}")
                elif cmd == "APPLY_LAST_CONFIG":
                    in_calibration = False
                    overlay.hide()
                    calib_idx = 0
                    intention_engine.calibration_points.clear()
                    config_manager.load_config()
                    intention_engine = IntentionEngine(config_manager)
                    print("[Main] Configuración guardada cargada. Omitiendo calibración visual.")
                    if event_server.loop and event_server.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            event_server.broadcast_message({"type": "TESTING", "event": "GAZE_CENTER", "confidence": 1.0}), 
                            event_server.loop
                        )
                elif cmd == "TEST_OK":
                    print("[Main] Modo Test Ok alternado. (Control de mouse on/off)")
                    if event_server.loop and event_server.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            event_server.broadcast_message({"type": "SYSTEM_COMMAND", "command": "TOGGLE_MOUSE"}), 
                            event_server.loop
                        )
                elif cmd == "CLOSE":
                    print("[Main] Cerrando por comando web.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return

            if key == ord('q'):
                break

            if in_calibration:
                target = calibration_sequence[calib_idx]
                
                # Enviar estado de calibración continuamente
                if event_server.loop and event_server.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        event_server.broadcast_message({"type": "CALIBRATION", "target": target.value}), 
                        event_server.loop
                    )
                
                # Dibujar círculo en el monitor
                overlay.draw_target(target)

                cv2.putText(image, f"CALIBRACION: Mira a {target.value}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(image, "Presiona 'ESPACIO' para confirmar", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                if key == ord(' '):
                    intention_engine.record_calibration_point(target, rel_x, rel_y)
                    
                    # Efecto flash
                    cv2.rectangle(image, (0, 0), (w, h), (255, 255, 255), -1)
                    cv2.imshow('NeuroCoder Studio - Eye Tracking Engine Debug', image)
                    cv2.waitKey(50)
                    
                    calib_idx += 1
                    if calib_idx >= len(calibration_sequence):
                        in_calibration = False
                        overlay.hide()
                        intention_engine.finish_calibration()
                        if event_server.loop and event_server.loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                event_server.broadcast_message({"type": "TESTING", "event": "GAZE_CENTER", "confidence": 1.0}), 
                                event_server.loop
                            )
            else:
                overlay.hide()
                # Modo normal
                raw_state = intention_engine.evaluate_intention(rel_x, rel_y)
                confirmed_state = stability_filter.filter_state(raw_state)
                
                if confirmed_state:
                    current_event = confirmed_state
                    if event_server.loop and event_server.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            event_server.broadcast_event(confirmed_state.value), 
                            event_server.loop
                        )
                else:
                    current_event = stability_filter.get_current_state()
                
                cv2.putText(image, f"X Rel: {rel_x:.3f} Y Rel: {rel_y:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                state_text = current_event.value.replace("GAZE_", "") if current_event else "..."
                cv2.putText(image, state_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            overlay.hide()
            if not in_calibration:
                raw_state = EyeEvent.LOST_FACE
                confirmed_state = stability_filter.filter_state(raw_state)
                if confirmed_state:
                    if event_server.loop and event_server.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            event_server.broadcast_event(confirmed_state.value), 
                            event_server.loop
                        )
            cv2.putText(image, "Rostro no detectado", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        cv2.imshow('NeuroCoder Studio - Eye Tracking Engine Debug', image)

    cap.release()
    cv2.destroyAllWindows()
    overlay.close()

if __name__ == "__main__":
    main()
