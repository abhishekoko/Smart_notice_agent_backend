# backend/services/ocr_service.py
import cv2
import pytesseract
import numpy as np
import os

# Windows Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_path: str) -> str:
    """Improved OCR for clean text extraction from screenshots."""
    
    if not os.path.exists(image_path):
        return ""

    img = cv2.imread(image_path)
    if img is None:
        return ""

    # 1. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Remove noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3. Upscale for sharper OCR (very important)
    gray = cv2.resize(gray, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_LINEAR)

    # 4. Adaptive Thresholding (best for screenshots)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 8
    )

    # 5. Sharpen the text
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    thresh = cv2.filter2D(thresh, -1, kernel)

    # 6. Tesseract config tuned for Notice/Document OCR
    config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1"

    text = pytesseract.image_to_string(thresh, config=config)

    # 7. Clean extra empty lines
    text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])

    return text.strip()
