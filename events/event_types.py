from enum import Enum

class EyeEvent(Enum):
    GAZE_LEFT = "GAZE_LEFT"
    GAZE_RIGHT = "GAZE_RIGHT"
    GAZE_UP = "GAZE_UP"
    GAZE_DOWN = "GAZE_DOWN"
    GAZE_CENTER = "GAZE_CENTER"
    BLINK = "BLINK"
    DWELL = "DWELL"
    LOST_FACE = "LOST_FACE"
