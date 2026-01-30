"""
Request 驗證器模組

提供 API 請求的驗證功能，包含 schema 檢查、大小限制與錯誤訊息。
"""

import os
import base64
import re
from typing import Tuple, Optional, Dict, Any


# 環境變數配置
MAX_IMAGE_BYTES = int(os.environ.get('MAX_IMAGE_BYTES', 10 * 1024 * 1024))  # 預設 10MB


class ValidationError(Exception):
    """驗證錯誤異常類別"""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RequestValidator:
    """
    請求驗證器類別
    
    負責驗證 API 請求的參數與格式。
    """
    
    @staticmethod
    def validate_passport_ocr_request(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        驗證護照 OCR 請求
        
        Args:
            data: 請求資料 dict
            
        Returns:
            Dict[str, Any]: 驗證後的參數
            
        Raises:
            ValidationError: 當驗證失敗時
        """
        if data is None:
            raise ValidationError("請求體必須為 JSON 格式")
        
        # 驗證必填欄位
        if 'image_base64' not in data:
            raise ValidationError("缺少必要參數：image_base64")
        
        image_base64 = data['image_base64']
        
        if not isinstance(image_base64, str):
            raise ValidationError("image_base64 必須為字串類型")
        
        if not image_base64.strip():
            raise ValidationError("image_base64 不可為空")
        
        # 解析 base64（支援 data-url 格式）
        base64_data = RequestValidator._extract_base64(image_base64)
        
        # 驗證 base64 大小
        RequestValidator._validate_base64_size(base64_data)
        
        # 驗證 base64 格式
        image_bytes = RequestValidator._decode_base64(base64_data)
        
        # 驗證選填參數
        min_conf = data.get('min_conf', 0.25)
        if not isinstance(min_conf, (int, float)) or not (0 <= min_conf <= 1):
            raise ValidationError("min_conf 必須為 0~1 之間的數值")
        
        max_det = data.get('max_det', 300)
        if not isinstance(max_det, int) or max_det <= 0:
            raise ValidationError("max_det 必須為正整數")
        
        return_debug = data.get('return_debug', False)
        if not isinstance(return_debug, bool):
            raise ValidationError("return_debug 必須為布林值")
        
        label_model_map = data.get('label_model_map')
        if label_model_map is not None and not isinstance(label_model_map, dict):
            raise ValidationError("label_model_map 必須為物件類型")
        
        return {
            'image_bytes': image_bytes,
            'min_conf': float(min_conf),
            'max_det': int(max_det),
            'return_debug': return_debug,
            'label_model_map': label_model_map
        }
    
    @staticmethod
    def _extract_base64(image_base64: str) -> str:
        """
        從可能包含 data-url 前綴的字串中提取純 base64 資料
        
        Args:
            image_base64: 原始 base64 字串（可能包含 data:image/...;base64, 前綴）
            
        Returns:
            str: 純 base64 字串
        """
        # 處理 data-url 格式：data:image/png;base64,xxxxx
        data_url_pattern = r'^data:image/[a-zA-Z0-9+.-]+;base64,'
        if re.match(data_url_pattern, image_base64, re.IGNORECASE):
            return re.sub(data_url_pattern, '', image_base64, flags=re.IGNORECASE)
        return image_base64.strip()
    
    @staticmethod
    def _validate_base64_size(base64_data: str) -> None:
        """
        驗證 base64 資料大小
        
        Args:
            base64_data: 純 base64 字串
            
        Raises:
            ValidationError: 當資料超過限制時
        """
        # base64 編碼後大小約為原始資料的 4/3 倍
        estimated_size = len(base64_data) * 3 // 4
        if estimated_size > MAX_IMAGE_BYTES:
            max_mb = MAX_IMAGE_BYTES / (1024 * 1024)
            raise ValidationError(f"圖片大小超過限制（最大 {max_mb:.1f}MB）")
    
    @staticmethod
    def _decode_base64(base64_data: str) -> bytes:
        """
        解碼 base64 字串
        
        Args:
            base64_data: 純 base64 字串
            
        Returns:
            bytes: 解碼後的二進位資料
            
        Raises:
            ValidationError: 當 base64 格式無效時
        """
        try:
            return base64.b64decode(base64_data)
        except Exception:
            raise ValidationError("無效的 base64 編碼格式")
