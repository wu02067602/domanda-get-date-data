"""
護照 OCR 服務模組

業務流程協調：decode base64 → yolo detect → crop → ocr rec → 回應
"""

import io
from typing import Dict, Any, List, Optional
from PIL import Image

from .model_registry import (
    ModelRegistry,
    ModelLoadError,
    YOLODetector,
    OCRRecognizer
)


class PassportOcrService:
    """
    護照 OCR 服務類別
    
    協調 YOLO 偵測與 PaddleOCR 辨識的完整流程。
    """
    
    def __init__(self):
        self._yolo_detector: Optional[YOLODetector] = None
    
    def process(
        self,
        image_bytes: bytes,
        min_conf: float = 0.25,
        max_det: int = 300,
        return_debug: bool = False,
        label_model_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        處理護照圖片，執行欄位偵測與文字辨識
        
        Args:
            image_bytes: 圖片二進位資料
            min_conf: YOLO 最低信心度閾值
            max_det: YOLO 最大偵測數量
            return_debug: 是否回傳除錯資訊
            label_model_map: 自訂 label → model 映射
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        # 1. 解碼圖片
        image = self._decode_image(image_bytes)
        
        # 2. YOLO 偵測
        yolo = ModelRegistry.get_yolo_detector()
        detections = yolo.detect(image, conf=min_conf, max_det=max_det)
        
        # 3. 對每個偵測結果進行 OCR 辨識
        results = []
        for detection in detections:
            result = self._process_detection(
                image,
                detection,
                label_model_map
            )
            results.append(result)
        
        response = {
            'success': True,
            'data': {
                'detections': results
            }
        }
        
        if return_debug:
            response['data']['debug'] = {
                'image_size': {'width': image.width, 'height': image.height},
                'total_detections': len(detections),
                'yolo_class_names': list(yolo.get_class_names().values())
            }
        
        return response
    
    def _decode_image(self, image_bytes: bytes) -> Image.Image:
        """
        解碼圖片二進位資料
        
        Args:
            image_bytes: 圖片二進位資料
            
        Returns:
            PIL.Image.Image: 解碼後的圖片
            
        Raises:
            ValueError: 當圖片格式無效時
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # 轉換為 RGB（移除 alpha channel）
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            return image
        except Exception as e:
            raise ValueError(f"無效的圖片格式：{e}")
    
    def _process_detection(
        self,
        image: Image.Image,
        detection: Dict[str, Any],
        label_model_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        處理單一偵測結果，進行裁切與 OCR 辨識
        
        Args:
            image: 原始圖片
            detection: YOLO 偵測結果
            label_model_map: label → model 映射
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        label = detection['label']
        bbox = detection['bbox']
        
        result = {
            'label': label,
            'confidence': detection['confidence'],
            'bbox': bbox,
            'text': None,
            'ocr_confidence': None,
            'rec_model': None
        }
        
        # 取得對應的 OCR 模型
        model_name = ModelRegistry.get_ocr_model_for_label(label, label_model_map)
        
        if model_name is None:
            # 沒有對應的 OCR 模型，跳過辨識
            result['rec_model'] = 'none'
            return result
        
        try:
            # 裁切圖片
            cropped = self._crop_image(image, bbox)
            
            # OCR 辨識
            recognizer = ModelRegistry.get_ocr_recognizer(model_name)
            text, ocr_conf = recognizer.recognize(cropped)
            
            result['text'] = text
            result['ocr_confidence'] = ocr_conf
            result['rec_model'] = model_name
            
        except ModelLoadError as e:
            result['rec_model'] = model_name
            result['error'] = str(e)
        except Exception as e:
            result['rec_model'] = model_name
            result['error'] = f"OCR 辨識失敗：{e}"
        
        return result
    
    def _crop_image(
        self,
        image: Image.Image,
        bbox: Dict[str, int]
    ) -> Image.Image:
        """
        根據 bbox 裁切圖片
        
        Args:
            image: 原始圖片
            bbox: 邊界框 {x1, y1, x2, y2}
            
        Returns:
            PIL.Image.Image: 裁切後的圖片
        """
        x1 = max(0, bbox['x1'])
        y1 = max(0, bbox['y1'])
        x2 = min(image.width, bbox['x2'])
        y2 = min(image.height, bbox['y2'])
        
        return image.crop((x1, y1, x2, y2))


# 全域服務實例
passport_ocr_service = PassportOcrService()
