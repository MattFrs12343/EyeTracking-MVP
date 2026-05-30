import asyncio
import websockets
import json
import pyautogui
import threading
import time
import ctypes
import atexit

# Configuración de seguridad de PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # Sin pausa artificial entre comandos

# Lista de IDs de los cursores estándar de Windows a ocultar
CURSOR_IDS = [
    32512,  # OCR_NORMAL (Standard arrow)
    32513,  # OCR_IBEAM (Text select)
    32514,  # OCR_WAIT (Busy/Hourglass)
    32515,  # OCR_CROSS (Precision select)
    32516,  # OCR_UP (Alternate select)
    32642,  # OCR_SIZENWSE (Diagonal resize 1)
    32643,  # OCR_SIZENESW (Diagonal resize 2)
    32644,  # OCR_SIZEWE (Horizontal resize)
    32645,  # OCR_SIZENS (Vertical resize)
    32646,  # OCR_SIZEALL (Move)
    32648,  # OCR_NO (Unavailable/Not allowed)
    32649,  # OCR_HAND (Link select)
    32650,  # OCR_APPSTARTING (Working in background)
]

def create_transparent_cursor():
    """Crea una máscara de bits transparente de 32x32 para simular un cursor invisible."""
    try:
        # AND mask: 1 conserva el color del fondo de la pantalla (transparente)
        # XOR mask: 0 conserva el color original del cursor (no altera nada)
        and_mask = bytes([0xFF] * 128)  # 32 * 32 bits = 1024 bits = 128 bytes
        xor_mask = bytes([0x00] * 128)
        
        # CreateCursor(hInst, xHotSpot, yHotSpot, nWidth, nHeight, pvANDPlane, pvXORPlane)
        return ctypes.windll.user32.CreateCursor(
            None, 0, 0, 32, 32, and_mask, xor_mask
        )
    except Exception as e:
        print(f"[MouseController] Error al crear cursor transparente: {e}")
        return None

def hide_global_cursor():
    """Reemplaza los cursores de Windows con el cursor transparente para ocultarlos globalmente."""
    print("[MouseController] Ocultando cursor de Windows globalmente...")
    try:
        for cursor_id in CURSOR_IDS:
            h_cursor = create_transparent_cursor()
            if h_cursor:
                # SetSystemCursor destruye el cursor que se le pasa, por lo que creamos uno nuevo cada vez
                ctypes.windll.user32.SetSystemCursor(h_cursor, cursor_id)
    except Exception as e:
        print(f"[MouseController] Error al ocultar cursor global: {e}")

def restore_global_cursor():
    """Fuerza a Windows a recargar los cursores estándar desde el registro (los restaura)."""
    print("[MouseController] Restaurando cursor de Windows original...")
    try:
        # SPI_SETCURSORS = 0x0057
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)
    except Exception as e:
        print(f"[MouseController] Error al restaurar cursor global: {e}")

# Registrar la restauración segura al apagarse el script de forma normal o con error
atexit.register(restore_global_cursor)

class MouseController:
    def __init__(self):
        self.current_state = "GAZE_CENTER"
        self.is_running = True
        self.is_tracking_active = False  # El tracking del mouse inicia apagado
        self.speed = 10  # Píxeles por frame de movimiento
        self.global_cursor_hidden = False
        
        # Iniciar el hilo del bucle de movimiento
        self.move_thread = threading.Thread(target=self.movement_loop, daemon=True)
        self.move_thread.start()

        # Registrar hotkey Failsafe F9 para restaurar el cursor en caso de emergencia
        try:
            import keyboard
            keyboard.add_hotkey('f9', lambda: self.toggle_global_cursor(False))
            print("[MouseController] Failsafe: Presiona 'F9' en tu teclado en cualquier momento para restaurar el cursor de Windows.")
        except Exception as e:
            print(f"[MouseController] No se pudo configurar el hotkey Failsafe F9: {e}")

    def toggle_tracking(self):
        self.is_tracking_active = not self.is_tracking_active
        if self.is_tracking_active:
            print("\n*** [MouseController] TRACKING DE MOUSE ACTIVADO ***")
        else:
            print("\n*** [MouseController] TRACKING DE MOUSE DESACTIVADO ***")
            self.current_state = "GAZE_CENTER"

    def toggle_global_cursor(self, active):
        if active and not self.global_cursor_hidden:
            hide_global_cursor()
            self.global_cursor_hidden = True
        elif not active and self.global_cursor_hidden:
            restore_global_cursor()
            self.global_cursor_hidden = False

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
                            elif data.get("command") == "TOGGLE_GLOBAL_CURSOR":
                                active = data.get("active", False)
                                self.toggle_global_cursor(active)
                                    
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
    finally:
        restore_global_cursor()
