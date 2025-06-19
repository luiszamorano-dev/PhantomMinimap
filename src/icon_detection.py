import cv2
import numpy as numpy
import pytesseract
from PIL import Image

class ChampionDetector:
    def __init__(self):
        sel.champion_db = ChampionDatabase()

    def detect_champions_loading_screen(self, screenshot):
        """Detecta campeones en la pantalla de carga usando OCR"""
        # 1. Recortar área de nombres de campeones
            # (coordenadas aproximadas, necesita calibración)
        team1_area = (300, 800, 600, 900)
        tream2_area = (1200,800, 1500, 900)

        # 2. Procesar imagen para OCR
        def preprocess_for_ocr(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            return thresh

        # 3. Ejecutar OCR
        team1_names = pytesseract.image_to_string(
            preprocess_for_ocr(screenshot[team1_area[1]:team1_area[3], team1_area[0]:team1_area[2]])
        ).split('\n')
        
        team2_names = pytesseract.image_to_string(
            preprocess_for_ocr(screenshot[team2_area[1]:team2_area[3], team2_area[0]:team2_area[2]])
        ).split('\n')
        
        return {
            "aliados": [name.strip() for name in team1_names if name.strip()],
            "enemigos": [name.strip() for name in team2_names if name.strip()]
        }