# Instrucciones para Matías — Integración Eye Tracking con NeuroCoder

## Contexto

Tu código de Eye Tracking ya está integrado dentro del proyecto NeuroCoder en la carpeta:
```
neurocoder-studio/eye-tracking/
```

Electron (NeuroCoder) lanza tu `main.py` usando el venv que está en esa misma carpeta. Todo funciona — la cámara se abre, calibra, y el mouse se mueve con la mirada.

El WebSocket que tu código levanta en `ws://127.0.0.1:8765` es la forma en que NeuroCoder recibe los eventos de mirada (GAZE_LEFT, GAZE_RIGHT, GAZE_UP, GAZE_DOWN, GAZE_CENTER).

---

## Lo que necesitamos de ti

### 1. Que el mouse_controller use `sys.executable` en vez de `"python"`

En `main.py`, donde lanzas el mouse_controller, cambia:
```python
subprocess.Popen(["python", mouse_client_path], shell=False)
```
Por:
```python
import sys
subprocess.Popen([sys.executable, mouse_client_path], shell=False)
```

**¿Por qué?** Porque en nuestra PC el Python del sistema es 3.10 pero tu venv fue creado con 3.12. `sys.executable` usa el mismo Python que está corriendo el script (el del venv), evitando errores de "Python not found".

---

### 2. Opción para saltar calibración si ya existe

Tu código ya tiene el comando `APPLY_LAST_CONFIG` que se envía por WebSocket y salta la calibración. NeuroCoder envía ese comando automáticamente al conectarse si detecta que `config/tracking.json` ya tiene datos de calibración.

**El problema:** A veces NeuroCoder se conecta al WebSocket antes de que tu servidor esté listo, y el comando no llega a tiempo. 

**Solución ideal:** Que `main.py` acepte un argumento `--skip-calibration` que cargue la última configuración directamente sin esperar el comando por WebSocket. Algo así:

```python
if '--skip-calibration' in sys.argv:
    config_manager.load_config()
    intention_engine = IntentionEngine(config_manager)
    in_calibration = False
    print("[Main] Calibración saltada, usando configuración guardada")
```

---

### 3. Opción para esconder el cursor del mouse

Ya nos dijiste que estás implementando esto. Lo que necesitamos:
- Que el cursor se esconda cuando el eye tracking está activo
- Que se pueda activar/desactivar (con una tecla o por WebSocket)
- Que al mover el mouse físicamente, el cursor reaparezca temporalmente (3 segundos) y luego se vuelva a esconder

---

### 4. Cómo entregar tu código actualizado

Cuando tengas la nueva versión:
1. Danos toda la carpeta (menos el `venv/`)
2. Nosotros la copiamos a `neurocoder-studio/eye-tracking/`
3. El `venv/` ya existe ahí con las dependencias instaladas (Python 3.10)

**Archivos que NO debes incluir:**
- `venv/` (ya lo tenemos)
- `__pycache__/` (se genera solo)

**Archivos que SÍ necesitamos:**
- `main.py`
- `clients/mouse_controller.py`
- `config/settings.json`
- `config/tracking.json`
- `core/`, `events/`, `filters/`, `gaze/`, `sockets/`, `tracking/`, `vision/`
- `face_landmarker.task`
- `requirements.txt` (si agregaste dependencias nuevas)

---

## Cómo funciona la integración

```
[Python - Eye Tracking]
    ↓ WebSocket (ws://127.0.0.1:8765)
    ↓ Envía: { type: "GAZE", event: "GAZE_LEFT" }
    ↓
[Electron - NeuroCoder]
    ↓ Recibe eventos
    ↓ Modo "Control del mouse": no hace nada (Python ya mueve el mouse)
    ↓ Modo "Navegación por bloques": mueve un foco visual entre botones/placeholders
```

### Eventos que NeuroCoder escucha del WebSocket:
- `GAZE_LEFT` → mover foco a la izquierda
- `GAZE_RIGHT` → mover foco a la derecha
- `GAZE_UP` → mover foco arriba
- `GAZE_DOWN` → mover foco abajo
- `GAZE_CENTER` → activar clic en el elemento enfocado

### Comandos que NeuroCoder envía por WebSocket:
- `{ "command": "APPLY_LAST_CONFIG" }` → saltar calibración
- `{ "command": "RECALIBRATE" }` → forzar recalibración

---

## Resumen de lo que necesitamos:

| # | Qué | Prioridad |
|---|-----|-----------|
| 1 | `sys.executable` en vez de `"python"` | Alta |
| 2 | Flag `--skip-calibration` | Alta |
| 3 | Cursor oculto con reactivación al mover mouse | Media |
| 4 | Entregar sin venv ni __pycache__ | Siempre |

---

## Preguntas para Matías:

1. ¿El `mouse_controller.py` necesita alguna dependencia nueva además de las que están en `requirements.txt`?
2. ¿El WebSocket envía los eventos GAZE_* continuamente o solo cuando cambia la dirección?
3. ¿Hay algún evento para "rostro perdido" (LOST_FACE) que debamos manejar?
