import numpy as np

class IrisTracker:
    def __init__(self):
        # Índices de landmarks para MediaPipe Face Mesh
        # Ojo izquierdo (del usuario)
        self.LEFT_EYE_POINTS = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.LEFT_IRIS = [474, 475, 476, 477]
        
        # Ojo derecho (del usuario)
        self.RIGHT_EYE_POINTS = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_IRIS = [469, 470, 471, 472]

    def _get_center(self, landmarks, indices, img_w, img_h):
        # Calcula el centro (x, y) promedio de una lista de puntos
        x_coords = [landmarks[i].x * img_w for i in indices]
        y_coords = [landmarks[i].y * img_h for i in indices]
        return np.mean(x_coords), np.mean(y_coords)

    def _get_bounding_box(self, landmarks, indices, img_w, img_h):
        # Calcula el bounding box (min_x, max_x, min_y, max_y) de una lista de puntos
        x_coords = [landmarks[i].x * img_w for i in indices]
        y_coords = [landmarks[i].y * img_h for i in indices]
        return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

    def calculate_relative_iris_position(self, face_landmarks, img_w, img_h):
        """
        Calcula la posición relativa del iris respecto a las comisuras fijas del ojo.
        Esto ignora los párpados y elimina casi todo el ruido y conflicto al mirar arriba/abajo.
        """
        # Calcular para el ojo izquierdo
        l_iris_cx, l_iris_cy = self._get_center(face_landmarks.landmark, self.LEFT_IRIS, img_w, img_h)
        
        # Puntos fijos de las comisuras: 362 (interior), 263 (exterior)
        l_inner_x = face_landmarks.landmark[362].x * img_w
        l_inner_y = face_landmarks.landmark[362].y * img_h
        l_outer_x = face_landmarks.landmark[263].x * img_w
        l_outer_y = face_landmarks.landmark[263].y * img_h
        
        l_center_x = (l_inner_x + l_outer_x) / 2.0
        l_center_y = (l_inner_y + l_outer_y) / 2.0
        l_width = max(abs(l_outer_x - l_inner_x), 1)

        # Calcular para el ojo derecho
        r_iris_cx, r_iris_cy = self._get_center(face_landmarks.landmark, self.RIGHT_IRIS, img_w, img_h)
        
        # Puntos fijos de las comisuras: 133 (interior), 33 (exterior)
        r_inner_x = face_landmarks.landmark[133].x * img_w
        r_inner_y = face_landmarks.landmark[133].y * img_h
        r_outer_x = face_landmarks.landmark[33].x * img_w
        r_outer_y = face_landmarks.landmark[33].y * img_h
        
        r_center_x = (r_inner_x + r_outer_x) / 2.0
        r_center_y = (r_inner_y + r_outer_y) / 2.0
        r_width = max(abs(r_outer_x - r_inner_x), 1)

        # Normalizar distancias basadas en el ancho fijo del ojo (sin párpados)
        l_rel_x = (l_iris_cx - l_center_x) / l_width
        l_rel_y = (l_iris_cy - l_center_y) / l_width
        
        r_rel_x = (r_iris_cx - r_center_x) / r_width
        r_rel_y = (r_iris_cy - r_center_y) / r_width

        # Promediar ambos ojos para mayor estabilidad
        avg_rel_x = (l_rel_x + r_rel_x) / 2.0
        avg_rel_y = (l_rel_y + r_rel_y) / 2.0

        # Centrar en 0.5 para mantener compatibilidad con el resto del sistema
        return 0.5 + avg_rel_x, 0.5 + avg_rel_y
