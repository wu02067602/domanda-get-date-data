"""
Temp Feature 模組測試

測試 /temp/* 端點的功能，包含健康檢查和錯誤處理。
使用 mock 機制避免載入實際模型。
"""

import pytest
import base64
import json
from unittest.mock import patch, MagicMock
import sys
import os

# 設置環境變數以啟用 temp_feature
os.environ['ENABLE_TEMP_FEATURE'] = '1'


def _get_fresh_app():
    """取得一個新的 Flask 應用實例（會清理舊模組）"""
    # 清理可能已載入的模組
    modules_to_remove = [m for m in list(sys.modules.keys()) if m.startswith('temp_feature') or m == 'app']
    for m in modules_to_remove:
        del sys.modules[m]
    
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


# 全域應用實例（避免重複載入）
_cached_app = None


@pytest.fixture
def app():
    """建立測試用 Flask 應用"""
    global _cached_app
    if _cached_app is None:
        _cached_app = _get_fresh_app()
    return _cached_app


@pytest.fixture
def client(app):
    """建立測試客戶端"""
    return app.test_client()


class TestTempHealth:
    """測試 /temp/health 端點"""
    
    def test_health_check_returns_healthy(self, client):
        """測試健康檢查端點回傳正確格式"""
        response = client.get('/temp/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['feature'] == 'temp_feature'


class TestPassportOcrValidation:
    """測試 /temp/ocr/passport 端點的驗證邏輯"""
    
    def test_missing_image_base64_returns_400(self, client):
        """測試缺少 image_base64 參數時回傳 400"""
        response = client.post(
            '/temp/ocr/passport',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'image_base64' in data['error']
    
    def test_empty_image_base64_returns_400(self, client):
        """測試 image_base64 為空時回傳 400"""
        response = client.post(
            '/temp/ocr/passport',
            json={'image_base64': ''},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_base64_returns_400(self, client):
        """測試無效的 base64 編碼時回傳 400"""
        response = client.post(
            '/temp/ocr/passport',
            json={'image_base64': 'not-valid-base64!!!'},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_non_json_body_returns_400(self, client):
        """測試非 JSON 請求體時回傳 400"""
        response = client.post(
            '/temp/ocr/passport',
            data='not json',
            content_type='text/plain'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_min_conf_returns_400(self, client):
        """測試無效的 min_conf 參數時回傳 400"""
        # 建立一個小型有效的 PNG base64
        valid_base64 = create_test_image_base64()
        
        response = client.post(
            '/temp/ocr/passport',
            json={
                'image_base64': valid_base64,
                'min_conf': 1.5  # 超出範圍
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'min_conf' in data['error']
    
    def test_invalid_max_det_returns_400(self, client):
        """測試無效的 max_det 參數時回傳 400"""
        valid_base64 = create_test_image_base64()
        
        response = client.post(
            '/temp/ocr/passport',
            json={
                'image_base64': valid_base64,
                'max_det': -1  # 負數
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'max_det' in data['error']


class TestPassportOcrWithMock:
    """使用 mock 測試 OCR 處理流程"""
    
    @patch('temp_feature.service.ModelRegistry')
    def test_successful_ocr_response_structure(self, mock_registry, client):
        """測試成功的 OCR 回應結構"""
        # 設定 mock YOLO 偵測器
        mock_yolo = MagicMock()
        mock_yolo.detect.return_value = [
            {
                'label': 'passport_no',
                'confidence': 0.95,
                'bbox': {'x1': 100, 'y1': 200, 'x2': 300, 'y2': 250}
            }
        ]
        mock_yolo.get_class_names.return_value = {0: 'passport_no'}
        
        # 設定 mock OCR 辨識器
        mock_ocr = MagicMock()
        mock_ocr.recognize.return_value = ('AB1234567', 0.98)
        
        mock_registry.get_yolo_detector.return_value = mock_yolo
        mock_registry.get_ocr_recognizer.return_value = mock_ocr
        mock_registry.get_ocr_model_for_label.return_value = 'alphanumeric'
        
        valid_base64 = create_test_image_base64()
        
        response = client.post(
            '/temp/ocr/passport',
            json={'image_base64': valid_base64},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'detections' in data['data']
    
    @patch('temp_feature.service.ModelRegistry')
    def test_ocr_with_debug_info(self, mock_registry, client):
        """測試帶有除錯資訊的 OCR 回應"""
        mock_yolo = MagicMock()
        mock_yolo.detect.return_value = []
        mock_yolo.get_class_names.return_value = {}
        
        mock_registry.get_yolo_detector.return_value = mock_yolo
        
        valid_base64 = create_test_image_base64()
        
        response = client.post(
            '/temp/ocr/passport',
            json={
                'image_base64': valid_base64,
                'return_debug': True
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'debug' in data['data']
        assert 'image_size' in data['data']['debug']


class TestDataUrlSupport:
    """測試 data-url 格式支援"""
    
    def test_data_url_format_is_accepted(self, client):
        """測試 data-url 格式的 base64 被接受"""
        from temp_feature.validator import RequestValidator
        
        # 建立有效的 PNG bytes
        png_bytes = create_minimal_png()
        base64_data = base64.b64encode(png_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_data}"
        
        # 測試驗證器可以正確解析 data-url
        validated = RequestValidator.validate_passport_ocr_request({
            'image_base64': data_url
        })
        
        assert 'image_bytes' in validated
        assert validated['image_bytes'] == png_bytes


class TestRequestValidator:
    """測試 RequestValidator 類別"""
    
    def test_validate_with_all_optional_params(self):
        """測試包含所有選填參數的驗證"""
        from temp_feature.validator import RequestValidator
        
        png_bytes = create_minimal_png()
        base64_data = base64.b64encode(png_bytes).decode('utf-8')
        
        validated = RequestValidator.validate_passport_ocr_request({
            'image_base64': base64_data,
            'min_conf': 0.5,
            'max_det': 100,
            'return_debug': True,
            'label_model_map': {'passport_no': 'english'}
        })
        
        assert validated['min_conf'] == 0.5
        assert validated['max_det'] == 100
        assert validated['return_debug'] is True
        assert validated['label_model_map'] == {'passport_no': 'english'}
    
    def test_validate_with_default_params(self):
        """測試使用預設參數的驗證"""
        from temp_feature.validator import RequestValidator
        
        png_bytes = create_minimal_png()
        base64_data = base64.b64encode(png_bytes).decode('utf-8')
        
        validated = RequestValidator.validate_passport_ocr_request({
            'image_base64': base64_data
        })
        
        assert validated['min_conf'] == 0.25
        assert validated['max_det'] == 300
        assert validated['return_debug'] is False
        assert validated['label_model_map'] is None


def create_minimal_png() -> bytes:
    """建立最小的有效 PNG 圖片（1x1 紅色像素）"""
    # 這是一個最小的有效 PNG 檔案
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk header
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # Width=1, Height=1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # Bit depth, color type, etc.
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,  # Compressed data
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,  # CRC
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82                      # IEND CRC
    ])


def create_test_image_base64() -> str:
    """建立測試用的 base64 圖片字串"""
    return base64.b64encode(create_minimal_png()).decode('utf-8')


class TestModelRegistry:
    """測試 ModelRegistry 類別"""
    
    def test_get_label_model_map_default(self):
        """測試取得預設 label-model 映射"""
        from temp_feature.model_registry import ModelRegistry
        
        mapping = ModelRegistry.get_label_model_map()
        
        assert 'passport_no' in mapping
        assert mapping['passport_no'] == 'alphanumeric'
        assert 'expiry_date' in mapping
        assert mapping['expiry_date'] == 'date'
    
    def test_get_label_model_map_with_override(self):
        """測試覆蓋預設映射"""
        from temp_feature.model_registry import ModelRegistry
        
        override = {'passport_no': 'english', 'custom_field': 'chinese'}
        mapping = ModelRegistry.get_label_model_map(override)
        
        assert mapping['passport_no'] == 'english'  # 覆蓋
        assert mapping['custom_field'] == 'chinese'  # 新增
        assert mapping['expiry_date'] == 'date'  # 保留原有
    
    def test_get_ocr_model_for_label(self):
        """測試根據 label 取得 OCR 模型"""
        from temp_feature.model_registry import ModelRegistry
        
        model = ModelRegistry.get_ocr_model_for_label('passport_no')
        assert model == 'alphanumeric'
        
        model = ModelRegistry.get_ocr_model_for_label('unknown_label')
        assert model is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
