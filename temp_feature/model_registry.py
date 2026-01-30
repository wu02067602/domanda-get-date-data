"""
模型註冊表模組

提供 YOLO 與 PaddleOCR 模型的 lazy singleton 載入機制。
支援 label → model 的映射。
"""

import os
import threading
import queue
from typing import Dict, Optional, Any, List, Tuple
from pathlib import Path

# 環境變數配置
OCR_MODELS_DIR = os.environ.get('OCR_MODELS_DIR', 'ocr_models')
YOLO_MODEL_PATH = os.environ.get(
    'YOLO_MODEL_PATH',
    'ocr_models/yolo/passport_field_detect/weights/best.pt'
)

# 預設 label → OCR 模型名稱映射
DEFAULT_LABEL_MODEL_MAP = {
    'passport_no': 'alphanumeric',
    'name_en': 'english',
    'name_zh': 'chinese',
    'nationality_en': 'english',
    'nationality_zh': 'chinese',
    'sex_en': 'english',
    'sex_zh': 'chinese',
    'birthdate': 'date',
    'issue_date': 'date',
    'expiry_date': 'date',
    'birth_place_en': 'english',
    'birth_place_zh': 'chinese',
    'issue_place_en': 'english',
    'issue_place_zh': 'chinese',
    'id_no': 'alphanumeric',
    'mrz_line1': 'alphanumeric',
    'mrz_line2': 'alphanumeric',
}

# 嘗試解析環境變數覆蓋的 mapping
try:
    import json
    env_map = os.environ.get('OCR_LABEL_MODEL_MAP')
    if env_map:
        DEFAULT_LABEL_MODEL_MAP.update(json.loads(env_map))
except (json.JSONDecodeError, TypeError):
    pass


class ModelLoadError(Exception):
    """模型載入錯誤異常類別"""
    pass


class InferenceQueue:
    """
    推論佇列類別
    
    使用鎖/佇列機制避免多執行緒併發造成不穩。
    """
    
    def __init__(self, maxsize: int = 100):
        self._queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()
        self._worker_started = False
    
    def submit(self, task_func, timeout: float = 30.0):
        """
        提交推論任務
        
        Args:
            task_func: 要執行的函數
            timeout: 等待超時時間（秒）
            
        Returns:
            任務執行結果
            
        Raises:
            Exception: 當任務執行失敗或超時時
        """
        result_container = {'result': None, 'exception': None}
        event = threading.Event()
        
        def wrapped_task():
            try:
                result_container['result'] = task_func()
            except Exception as e:
                result_container['exception'] = e
            finally:
                event.set()
        
        try:
            self._queue.put(wrapped_task, timeout=5)
        except queue.Full:
            raise Exception("推論佇列已滿，請稍後再試")
        
        with self._lock:
            if not self._worker_started:
                threading.Thread(target=self._process_queue, daemon=True).start()
                self._worker_started = True
        
        if not event.wait(timeout=timeout):
            raise Exception("推論超時")
        
        if result_container['exception']:
            raise result_container['exception']
        
        return result_container['result']
    
    def _process_queue(self):
        """處理佇列中的任務"""
        while True:
            try:
                task = self._queue.get(timeout=1)
                task()
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"推論佇列處理錯誤: {e}")
                try:
                    self._queue.task_done()
                except ValueError:
                    pass


class YOLODetector:
    """
    YOLO 偵測器類別（Lazy Singleton）
    
    使用 ultralytics YOLO 進行護照欄位偵測。
    """
    
    _instance = None
    _lock = threading.Lock()
    _inference_queue = InferenceQueue()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def _ensure_loaded(self):
        """確保模型已載入"""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            try:
                from ultralytics import YOLO
                
                model_path = Path(YOLO_MODEL_PATH)
                if not model_path.exists():
                    raise ModelLoadError(f"YOLO 模型檔案不存在：{model_path}")
                
                self._model = YOLO(str(model_path))
                self._initialized = True
                print(f"YOLO 模型載入完成：{model_path}")
                
            except ImportError:
                raise ModelLoadError("無法載入 ultralytics 套件")
            except Exception as e:
                raise ModelLoadError(f"YOLO 模型載入失敗：{e}")
    
    def detect(
        self,
        image,
        conf: float = 0.25,
        max_det: int = 300
    ) -> List[Dict[str, Any]]:
        """
        執行物件偵測
        
        Args:
            image: PIL Image 或 numpy array
            conf: 最低信心度閾值
            max_det: 最大偵測數量
            
        Returns:
            List[Dict]: 偵測結果列表，每個元素包含：
                - label: 類別名稱
                - confidence: 信心度
                - bbox: {x1, y1, x2, y2}
        """
        self._ensure_loaded()
        
        def _do_detect():
            results = self._model(
                image,
                conf=conf,
                max_det=max_det,
                verbose=False
            )
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    label = result.names.get(class_id, f"class_{class_id}")
                    
                    detections.append({
                        'label': label,
                        'confidence': confidence,
                        'bbox': {
                            'x1': int(x1),
                            'y1': int(y1),
                            'x2': int(x2),
                            'y2': int(y2)
                        }
                    })
            
            return detections
        
        return self._inference_queue.submit(_do_detect)
    
    def get_class_names(self) -> Dict[int, str]:
        """取得類別名稱映射"""
        self._ensure_loaded()
        return self._model.names


class OCRRecognizer:
    """
    PaddleOCR 文字辨識器類別
    
    支援多種模型（english, chinese, date, alphanumeric）。
    """
    
    _instances: Dict[str, 'OCRRecognizer'] = {}
    _lock = threading.Lock()
    _inference_queue = InferenceQueue()
    
    # 模型配置
    MODEL_CONFIGS = {
        'english': {
            'model_dir': 'english/inference',
            'char_dict': 'english/inference/dict.txt',
            'use_space_char': True,
        },
        'chinese': {
            'model_dir': 'chinese/inference',
            'char_dict': 'chinese/inference/dict.txt',
            'use_space_char': True,
        },
        'date': {
            'model_dir': 'date/inference',
            'char_dict': 'date/inference/dict.txt',
            'use_space_char': True,
        },
        'alphanumeric': {
            'model_dir': 'alphanumeric/inference',
            'char_dict': 'alphanumeric/inference/dict.txt',
            'use_space_char': False,
        },
    }
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._initialized = False
    
    @classmethod
    def get_instance(cls, model_name: str) -> 'OCRRecognizer':
        """
        取得 OCR 辨識器實例（Lazy Singleton per model_name）
        
        Args:
            model_name: 模型名稱（english, chinese, date, alphanumeric）
            
        Returns:
            OCRRecognizer: 辨識器實例
        """
        if model_name not in cls._instances:
            with cls._lock:
                if model_name not in cls._instances:
                    cls._instances[model_name] = cls(model_name)
        return cls._instances[model_name]
    
    def _ensure_loaded(self):
        """確保模型已載入"""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            if self.model_name not in self.MODEL_CONFIGS:
                raise ModelLoadError(f"不支援的 OCR 模型：{self.model_name}")
            
            config = self.MODEL_CONFIGS[self.model_name]
            models_dir = Path(OCR_MODELS_DIR)
            
            model_dir = models_dir / config['model_dir']
            char_dict = models_dir / config['char_dict']
            
            if not model_dir.exists():
                raise ModelLoadError(f"OCR 模型目錄不存在：{model_dir}")
            
            if not char_dict.exists():
                raise ModelLoadError(f"OCR 字典檔案不存在：{char_dict}")
            
            try:
                from paddleocr import PaddleOCR
                
                # 建立只做辨識（rec）的 PaddleOCR 實例
                self._model = PaddleOCR(
                    use_gpu=False,  # Cloud Run CPU 環境
                    use_angle_cls=False,
                    use_det=False,  # 不做偵測，只做辨識
                    rec_model_dir=str(model_dir),
                    rec_char_dict_path=str(char_dict),
                    use_space_char=config['use_space_char'],
                    show_log=False,
                )
                
                self._initialized = True
                print(f"OCR 模型載入完成：{self.model_name}")
                
            except ImportError:
                raise ModelLoadError("無法載入 paddleocr 套件")
            except Exception as e:
                raise ModelLoadError(f"OCR 模型載入失敗：{e}")
    
    def recognize(self, image) -> Tuple[str, float]:
        """
        執行文字辨識
        
        Args:
            image: PIL Image 或 numpy array（裁切後的圖片）
            
        Returns:
            Tuple[str, float]: (辨識文字, 信心度)
        """
        self._ensure_loaded()
        
        def _do_recognize():
            import numpy as np
            from PIL import Image
            
            # 確保是 numpy array
            if isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                img_array = image
            
            # PaddleOCR ocr() 方法進行辨識
            result = self._model.ocr(img_array, det=False, rec=True, cls=False)
            
            if not result or not result[0]:
                return ('', 0.0)
            
            # result[0] 是辨識結果列表
            rec_result = result[0]
            if isinstance(rec_result, list) and len(rec_result) > 0:
                # 格式：[[text, confidence], ...]
                if isinstance(rec_result[0], (list, tuple)) and len(rec_result[0]) >= 2:
                    text = rec_result[0][0]
                    conf = float(rec_result[0][1])
                    return (text, conf)
            
            return ('', 0.0)
        
        return self._inference_queue.submit(_do_recognize)


class ModelRegistry:
    """
    模型註冊表
    
    提供統一的模型存取介面。
    """
    
    @staticmethod
    def get_yolo_detector() -> YOLODetector:
        """取得 YOLO 偵測器"""
        return YOLODetector()
    
    @staticmethod
    def get_ocr_recognizer(model_name: str) -> OCRRecognizer:
        """取得 OCR 辨識器"""
        return OCRRecognizer.get_instance(model_name)
    
    @staticmethod
    def get_label_model_map(override: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        取得 label → model 映射
        
        Args:
            override: 覆蓋預設映射的自訂映射
            
        Returns:
            Dict[str, str]: label → model_name 映射
        """
        result = DEFAULT_LABEL_MODEL_MAP.copy()
        if override:
            result.update(override)
        return result
    
    @staticmethod
    def get_ocr_model_for_label(
        label: str,
        label_model_map: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        根據 label 取得對應的 OCR 模型名稱
        
        Args:
            label: YOLO 偵測到的標籤
            label_model_map: 自訂映射（可選）
            
        Returns:
            Optional[str]: OCR 模型名稱，若無對應則為 None
        """
        mapping = ModelRegistry.get_label_model_map(label_model_map)
        return mapping.get(label)
