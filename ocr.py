import cv2
from paddleocr import PaddleOCR, draw_ocr


def _process_captcha(image):
    if image is None:
        print("Error: Could not open or read image file")
        return None

    # 0.裁剪图片
    h, w = image.shape[:2]
    start_row, start_col = int(h * 0.05), int(w * 0.25)
    end_row, end_col = int(h * 0.95), int(w * 0.75)
    image = image[start_row:end_row, start_col:end_col]
    return image


def ocr_image(image):
    ocr = PaddleOCR(lang="en")
    if image is None:
        raise ValueError("Image not found or invalid format.")
    image = _process_captcha(image)
    output = ocr.ocr(image, det=False, cls=False)
    result = ""
    for idx in range(len(output)):
        res = output[idx]
        if res is None:
            continue
        for line in res:
            data = line[0]
            result += data
    return result
