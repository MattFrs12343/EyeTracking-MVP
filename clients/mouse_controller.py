import asyncio
import websockets
import json
import pyautogui
import threading
import time

# Configuración de seguridad de PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # Sin pausa artificial entre comandos

class MouseController:
    def __init__(self):
        self.current_state = "GAZE_CENTER"
        self.is_running = True
        self.is_tracking_active = False  # El tracking del mouse inicia apagado
        self.speed = 10  # Píxeles por frame de movimiento
        
        # Iniciar el hilo del bucle de movimiento
        self.move_thread = threading.Thread(target=self.movement_loop, daemon=True)
        self.move_thread.start()

    def toggle_tracking(self):
        self.is_tracking_active = not self.is_tracking_active
        if self.is_tracking_active:
            print("\n*** [MouseController] TRACKING DE MOUSE ACTIVADO ***")
        else:
            print("\n*** [MouseController] TRACKING DE MOUSE DESACTIVADO ***")
            self.current_state = "GAZE_CENTER"

    def movement_loop(self):
        print("[MouseController] Bucle de movimiento iniciado.")
        while self.is_running:
            if self.is_tracking_active:
                try:
                    if self.current_state == "GAZE_LEFT":
                        pyautogui.moveRel(-self.speed, 0, _pause=False)
                    elif self.current_state == "GAZE_RIGHT":
                        pyautogui.moveRel(self.speed, 0, _pause=False)
                    elif self.current_state == "GAZE_UP":
                        pyautogui.moveRel(0, -self.speed, _pause=False)
                    elif self.current_state == "GAZE_DOWN":
                        pyautogui.moveRel(0, self.speed, _pause=False)
                except pyautogui.FailSafeException:
                    print("\n[!] FAILSAFE ACTIVADO por mover el ratón a la esquina.")
                    print("[!] Apagando tracking por seguridad. Usa los botones web para volver a activarlo.")
                    self.is_tracking_active = False
                    self.current_state = "GAZE_CENTER"
            
            # Correr aproximadamente a 60 ciclos por segundo
            time.sleep(1.0 / 60.0)

    async def connect_to_engine(self):
        uri = "ws://127.0.0.1:8765"
        print(f"[MouseController] Conectando al motor en {uri}...")
    
        while self.is_running:
            try:
                async with websockets.connect(uri) as websocket:
                    print("[MouseController] ¡Conectado al Motor de Eye Tracking!")
                    
                    async for message in websocket:
                        data = json.loads(message)
                        
                        if data.get("type") == "TESTING":
                            event = data.get("event")
                            # Si perdemos el rostro o cerramos los ojos, detenemos el mouse por seguridad
                            if event in ["LOST_FACE", "BLINK", "GAZE_CENTER"]:
                                self.current_state = "GAZE_CENTER"
                            else:
                                self.current_state = event
                                
                        elif data.get("type") == "CALIBRATION":
                            # No mover el mouse durante la calibración
                            self.current_state = "GAZE_CENTER"
                            
                        elif data.get("type") == "SYSTEM_COMMAND":
                            if data.get("command") == "TOGGLE_MOUSE":
                                self.toggle_tracking()
                                    
            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError):
                print("[MouseController] Motor no encontrado. Reintentando en 2 segundos...")
                self.current_state = "GAZE_CENTER"
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[MouseController] Error: {e}")
                self.current_state = "GAZE_CENTER"
                await asyncio.sleep(2)

    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    print("========================================")
    print("    NEUROCODER EYE TRACKING - MOUSE     ")
    print("========================================")
    print("Instrucción de Seguridad (FailSafe):")
    print("Mueve físicamente tu ratón a cualquiera")
    print("de las 4 esquinas de tu monitor si")
    print("pierdes el control. Esto forzará una parada.")
    print("----------------------------------------")
    print("ATAJO DESDE LA WEB:")
    print("Usa los botones 'Test' u 'Ok' en la web")
    print("para ACTIVAR/DESACTIVAR el mouse.")
    print("========================================")
    
    controller = MouseController()
    try:
        asyncio.run(controller.connect_to_engine())
    except KeyboardInterrupt:
        print("[MouseController] Cerrando...")
        controller.stop()
