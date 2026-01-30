"""
Flask 日期 API 應用程式

此應用程式提供一個 POST API 端點，用於計算固定月份的日期區間。
"""

from flask import Flask, request, jsonify
from date_calculator import DateCalculator, DateValidator
from holiday_calculator import HolidayDateCalculator
from interfaces import IFixedMonthDateCalculator, IDateValidator
from typing import Dict, Any
import requests
import queue
import threading
from functools import wraps


app = Flask(__name__)

# 建立佇列用於管理 holiday_calculator 的請求
holiday_request_queue = queue.Queue(maxsize=200)
holiday_queue_lock = threading.Lock()


def queue_task(func):
    """
    裝飾器：將任務加入佇列並依序執行，避免併發問題。
    
    Args:
        func (Callable): 被裝飾的函數
    
    Returns:
        Callable: 包裝後的函數
    
    Examples:
        @queue_task
        def some_function():
            pass
    
    Raises:
        queue.Full: 當佇列已滿時
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result_container = {'result': None, 'exception': None}
        event = threading.Event()
        
        def task():
            try:
                result_container['result'] = func(*args, **kwargs)
            except Exception as e:
                result_container['exception'] = e
            finally:
                event.set()
        
        # 將任務加入佇列
        try:
            holiday_request_queue.put(task, timeout=5)
        except queue.Full:
            raise Exception("系統繁忙，請稍後再試")
        
        # 啟動佇列處理
        with holiday_queue_lock:
            if not hasattr(wrapper, '_worker_started') or not wrapper._worker_started:
                threading.Thread(target=_process_queue, daemon=True).start()
                wrapper._worker_started = True
        
        # 等待任務完成
        event.wait()
        
        if result_container['exception']:
            raise result_container['exception']
        
        return result_container['result']
    
    return wrapper


def _process_queue():
    """
    處理佇列中的任務。
    
    Args:
        無
    
    Returns:
        None
    
    Examples:
        不直接調用，由 queue_task 裝飾器自動啟動
    
    Raises:
        不拋出異常
    """
    while True:
        try:
            task = holiday_request_queue.get(timeout=1)
            task()
            holiday_request_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            # 記錄錯誤但不中斷處理
            print(f"處理佇列任務時發生錯誤: {e}")
            holiday_request_queue.task_done()


class DateAPIService:
    """
    日期 API 服務類別
    
    負責協調日期驗證和計算邏輯。
    """

    def __init__(self, calculator: IFixedMonthDateCalculator, validator: IDateValidator):
        """
        初始化日期 API 服務。
        
        Args:
            calculator (DateCalculator): 日期計算器實例
            validator (DateValidator): 日期驗證器實例
        
        Returns:
            None
        
        Examples:
            >>> calculator = DateCalculator()
            >>> validator = DateValidator()
            >>> service = DateAPIService(calculator, validator)
        
        Raises:
            TypeError: 當傳入的參數類型不正確時
        """
        self.calculator = calculator
        self.validator = validator

    def process_request(self, data: Dict) -> tuple[Dict[str, Any], int]:
        """
        處理日期計算請求。
        
        Args:
            data (Dict): 請求數據，應包含 month_offset、dep_day、return_day
        
        Returns:
            tuple[Dict[str, Any], int]: (響應數據, HTTP 狀態碼)
        
        Examples:
            >>> service = DateAPIService(DateCalculator(), DateValidator())
            >>> response, status = service.process_request({"month_offset": 2, "dep_day": 5, "return_day": 10})
            >>> status
            200
        
        Raises:
            不拋出異常，錯誤會在響應中返回
        """
        # 驗證輸入
        is_valid, error_message = self.validator.validate_input(data)
        if not is_valid:
            return {"error": error_message}, 400
        
        # 計算日期
        try:
            result = self.calculator.calculate_dates(
                int(data["month_offset"]),
                int(data["dep_day"]),
                int(data["return_day"])
            )
            return {
                "success": True,
                "data": result
            }, 200
        except ValueError as e:
            return {"error": str(e)}, 400


# 初始化服務
date_service = DateAPIService(DateCalculator(), DateValidator())
holiday_calculator = HolidayDateCalculator()


@app.route('/calculate_dates', methods=['POST'])
def calculate_dates():
    """
    計算日期區間的 API 端點。
    
    接收 POST 請求，計算基於月份偏移量的日期區間。
    
    Args:
        無直接參數，從 request.json 獲取：
        - month_offset (int): 月份偏移量
        - dep_day (int): 出發日期天數
        - return_day (int): 回程日期天數
    
    Returns:
        JSON 響應，格式為：
        成功時：
        {
            "success": true,
            "data": {
                "departure_date": "YYYY-MM-DD",
                "return_date": "YYYY-MM-DD",
                "target_year": YYYY,
                "target_month": MM
            }
        }
        失敗時：
        {
            "error": "錯誤訊息"
        }
    
    Examples:
        POST /calculate_dates
        Body: {"month_offset": 2, "dep_day": 5, "return_day": 10}
        Response: {"success": true, "data": {"departure_date": "2025-12-05", ...}}
    
    Raises:
        不直接拋出異常，錯誤會在 JSON 響應中返回
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "請求體必須為 JSON 格式"}), 400
    
    response, status_code = date_service.process_request(data)
    return jsonify(response), status_code


@app.route('/health', methods=['GET'])
def health_check():
    """
    健康檢查端點。
    
    用於檢查 API 服務是否正常運行。
    
    Args:
        無
    
    Returns:
        JSON 響應，格式為：{"status": "healthy"}
    
    Examples:
        GET /health
        Response: {"status": "healthy"}
    
    Raises:
        不拋出異常
    """
    return jsonify({"status": "healthy"}), 200


@queue_task
def _calculate_holiday_dates_with_queue(month_offset: int) -> Dict[str, Any]:
    """
    使用佇列機制計算節日日期（內部函數）。
    
    Args:
        month_offset (int): 月份偏移量
    
    Returns:
        Dict[str, Any]: 計算結果
    
    Examples:
        不直接調用，由 calculate_holiday_dates API 端點使用
    
    Raises:
        ValueError: 當參數無效時
        requests.RequestException: 當 API 請求失敗時
    """
    return holiday_calculator.calculate_dates(month_offset)


@app.route('/calculate_holiday_dates', methods=['POST'])
def calculate_holiday_dates():
    """
    計算節日日期區間的 API 端點。
    
    接收 POST 請求，計算基於月份偏移量的節假日日期區間。
    使用佇列機制避免併發問題。
    
    Args:
        無直接參數，從 request.json 獲取：
        - month_offset (int): 月份偏移量
    
    Returns:
        JSON 響應，格式為：
        成功時：
        {
            "success": true,
            "data": {
                "target_year": YYYY,
                "target_month": MM,
                "holidays": [
                    {
                        "holiday_name": "節日名稱",
                        "holiday_date": "YYYY-MM-DD",
                        "departure_date": "YYYY-MM-DD",
                        "return_date": "YYYY-MM-DD",
                        "weekday": "星期幾"
                    }
                ]
            }
        }
        失敗時：
        {
            "error": "錯誤訊息"
        }
    
    Examples:
        POST /calculate_holiday_dates
        Body: {"month_offset": 2}
        Response: {"success": true, "data": {...}}
    
    Raises:
        不直接拋出異常，錯誤會在 JSON 響應中返回
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "請求體必須為 JSON 格式"}), 400
    
    # 驗證必要參數
    if "month_offset" not in data:
        return jsonify({"error": "缺少必要參數：month_offset"}), 400
    
    try:
        month_offset = int(data["month_offset"])
    except (ValueError, TypeError):
        return jsonify({"error": "month_offset 必須為整數類型"}), 400
    
    # 驗證數值範圍
    if month_offset < 0:
        return jsonify({"error": "month_offset 必須為非負整數"}), 400
    
    # 使用佇列機制計算節日日期
    try:
        result = _calculate_holiday_dates_with_queue(month_offset)
        return jsonify({
            "success": True,
            "data": result
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.RequestException as e:
        return jsonify({"error": f"無法獲取節假日資料：{str(e)}"}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
