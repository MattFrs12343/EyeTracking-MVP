import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FaceMeshDetector:
    def __init__(self, model_path='face_landmarker.task', num_faces=1):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=num_faces
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)

    def process(self, image):
        # MediaPipe Tasks espera mp.Image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Procesar
        detection_result = self.detector.detect(mp_image)
        return detection_result

    def draw_landmarks(self, image, results):
        if not results.face_landmarks:
            return image
            
        for face_landmarks in results.face_landmarks:
            h, w, _ = image.shape
            
            # Dibujar los puntos del ojo e iris para depurar
            for i in [474, 475, 476, 477, 469, 470, 471, 472]:
                if i < len(face_landmarks):
                    x = int(face_landmarks[i].x * w)
                    y = int(face_landmarks[i].y * h)
                    cv2.circle(image, (x, y), 2, (0, 255, 255), -1)
                    
        return image
