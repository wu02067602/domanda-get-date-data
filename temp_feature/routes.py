"""
Temp Feature 路由模組

定義 /temp/* 端點。
"""

from flask import jsonify, request

from . import bp
from .validator import RequestValidator, ValidationError
from .service import passport_ocr_service
from .model_registry import ModelLoadError


@bp.route('/health', methods=['GET'])
def health():
    """
    健康檢查端點
    
    Returns:
        JSON 響應：{"status": "healthy", "feature": "temp_feature"}
    """
    return jsonify({
        'status': 'healthy',
        'feature': 'temp_feature'
    }), 200


@bp.route('/ocr/passport', methods=['POST'])
def ocr_passport():
    """
    護照 OCR 端點
    
    接收 POST 請求，執行護照欄位偵測與文字辨識。
    
    Request Body (JSON):
        - image_base64 (必填): Base64 編碼的圖片，支援 data-url 格式
        - min_conf (選填): YOLO 最低信心度，預設 0.25
        - max_det (選填): YOLO 最大偵測數量，預設 300
        - return_debug (選填): 是否回傳除錯資訊，預設 false
        - label_model_map (選填): 自訂 label → model 映射
    
    Returns:
        成功時：
        {
            "success": true,
            "data": {
                "detections": [
                    {
                        "label": "passport_no",
                        "confidence": 0.95,
                        "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 250},
                        "text": "AB1234567",
                        "ocr_confidence": 0.98,
                        "rec_model": "alphanumeric"
                    },
                    ...
                ]
            }
        }
        
        失敗時：
        {
            "error": "錯誤訊息"
        }
    """
    try:
        # 嘗試解析 JSON
        try:
            data = request.get_json(force=False, silent=False)
        except Exception:
            return jsonify({'error': '請求體必須為 JSON 格式'}), 400
        
        # 驗證請求
        validated = RequestValidator.validate_passport_ocr_request(data)
        
        # 執行 OCR 處理
        result = passport_ocr_service.process(
            image_bytes=validated['image_bytes'],
            min_conf=validated['min_conf'],
            max_det=validated['max_det'],
            return_debug=validated['return_debug'],
            label_model_map=validated['label_model_map']
        )
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message}), e.status_code
    
    except ModelLoadError as e:
        return jsonify({'error': str(e)}), 500
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        return jsonify({'error': f'內部錯誤：{str(e)}'}), 500


@bp.errorhandler(ValidationError)
def handle_validation_error(error):
    """處理驗證錯誤"""
    return jsonify({'error': error.message}), error.status_code


@bp.errorhandler(404)
def handle_not_found(error):
    """處理 404 錯誤"""
    return jsonify({'error': '端點不存在'}), 404


@bp.errorhandler(500)
def handle_internal_error(error):
    """處理 500 錯誤"""
    return jsonify({'error': '內部伺服器錯誤'}), 500
