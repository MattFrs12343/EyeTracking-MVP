# NeuroCoder Eye Tracking — MVP

Proyecto MVP para seguimiento de la mirada (eye-tracking) usando MediaPipe, OpenCV y un servidor WebSocket.

## Descripción
- **Propósito:** Capturar la posición del iris y traducirla en eventos de mirada (arriba/abajo/izquierda/derecha/centro). Incluye calibración visual y un cliente opcional que controla el ratón.
- **Stack:** Python, OpenCV, MediaPipe Tasks, websockets, pyautogui.

## Características
- Calibración interactiva con overlay de monitor.
- Motor de intención (`gaze/intention_engine.py`) que convierte las posiciones relativas en eventos discretos.
- Tracking de iris robusto (`tracking/iris_tracker.py`).
- Servidor WebSocket para comunicar eventos y recibir comandos (`sockets/server.py`).
- Cliente de control de ratón opcional (`clients/mouse_controller.py`).

## Requisitos
Instala dependencias (recomendado en un entorno virtual):

```bash
pip install -r requirements.txt
```

## Ejecución rápida
1. Ajusta la cámara y parámetros si lo deseas en `config/tracking.json` o `config/settings.json`.
2. Ejecuta la aplicación principal:

```bash
python main.py
```

El frontend simple está en `frontend/index.html` y se abre automáticamente si existe. El servidor WebSocket arranca en `ws://127.0.0.1:8765`.

## Archivos importantes
- `main.py`: Punto de entrada, flujo principal y calibración.
- `requirements.txt`: Dependencias del proyecto.
- `config/settings.json`: Ajustes generales (cámara, calibración, performance).
- `config/tracking.json`: Configuración del motor de intención (umbral, stability, camera_index).
- `vision/face_mesh.py`: Envoltura de MediaPipe FaceLandmarker.
- `tracking/iris_tracker.py`: Cálculo de posición relativa del iris.
- `gaze/intention_engine.py`: Lógica de conversión de coordenadas a eventos.
- `sockets/server.py`: Servidor WebSocket para eventos y comandos.
- `clients/mouse_controller.py`: Cliente que mueve el ratón basado en eventos.
- `face_landmarker.task`: Modelo binario de MediaPipe usado por el detector de rostro.

## Configuración
- Cambia la cámara por defecto en `config/tracking.json` (`camera_index`).
- Durante la calibración presiona `ESPACIO` para confirmar cada punto; `q` para salir.

## Seguridad y notas
- `clients/mouse_controller.py` usa `pyautogui.FAILSAFE = True`: mueve el ratón a una esquina para detener el control automáticamente.
- Ejecuta con permisos de usuario; algunos entornos Windows pueden necesitar ajustes de cámara o permisos.

## Siguientes pasos sugeridos
- Añadir instrucciones de instalación detalladas por plataforma (Windows/Linux/Mac).
- Añadir tests unitarios y un script de CI.
- Mejorar el frontend para visualizar estado y controlar calibración desde la web.

---
Generado por el análisis del repositorio.
