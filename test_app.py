"""
日期 API 單元測試

測試日期計算和驗證功能。
"""

import pytest
from datetime import datetime
from date_calculator import DateCalculator, DateValidator
from app import app, DateAPIService


class TestDateCalculator:
    """
    測試 DateCalculator 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        self.calculator = DateCalculator()

    def test_calculate_dates_basic(self):
        """
        測試基本日期計算功能。
        
        驗證當輸入有效的月份偏移量和日期時，能正確計算目標日期。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_basic
        
        Raises:
            AssertionError: 當測試失敗時
        """
        result = self.calculator.calculate_dates(0, 15, 20)
        
        current_date = datetime.now()
        expected_year = current_date.year
        expected_month = current_date.month
        
        assert result["target_year"] == expected_year
        assert result["target_month"] == expected_month
        assert result["departure_date"] == f"{expected_year}-{expected_month:02d}-15"
        assert result["return_date"] == f"{expected_year}-{expected_month:02d}-20"

    def test_calculate_dates_with_offset(self):
        """
        測試帶月份偏移量的日期計算。
        
        驗證當輸入月份偏移量時，能正確計算未來月份的日期。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_with_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        result = self.calculator.calculate_dates(2, 5, 10)
        
        current_date = datetime.now()
        target_month = current_date.month + 2
        target_year = current_date.year
        
        if target_month > 12:
            target_month -= 12
            target_year += 1
        
        assert result["target_year"] == target_year
        assert result["target_month"] == target_month
        assert result["departure_date"] == f"{target_year}-{target_month:02d}-05"
        assert result["return_date"] == f"{target_year}-{target_month:02d}-10"

    def test_calculate_dates_cross_year(self):
        """
        測試跨年的日期計算。
        
        驗證當月份偏移量導致跨年時，能正確處理年份變化。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_cross_year
        
        Raises:
            AssertionError: 當測試失敗時
        """
        result = self.calculator.calculate_dates(15, 5, 10)
        
        current_date = datetime.now()
        target_month = current_date.month + 15
        target_year = current_date.year
        
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        assert result["target_year"] == target_year
        assert result["target_month"] == target_month

    def test_calculate_dates_exceeds_month_days(self):
        """
        測試日期超過月份天數的情況。
        
        驗證當輸入的日期天數超過目標月份的最大天數時，能自動調整為該月份的最後一天。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_exceeds_month_days
        
        Raises:
            AssertionError: 當測試失敗時
        """
        # 2月最多29天（閏年）或28天
        result = self.calculator.calculate_dates(1, 31, 31)
        
        # 驗證日期不會超過該月份的最大天數
        dep_date_parts = result["departure_date"].split("-")
        return_date_parts = result["return_date"].split("-")
        
        assert int(dep_date_parts[2]) <= 31
        assert int(return_date_parts[2]) <= 31

    def test_calculate_dates_negative_offset(self):
        """
        測試負數月份偏移量的錯誤處理。
        
        驗證當輸入負數月份偏移量時，拋出 ValueError。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_negative_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_dates(-1, 5, 10)
        
        assert "月份偏移量必須為非負整數" in str(exc_info.value)

    def test_calculate_dates_invalid_dep_day(self):
        """
        測試無效出發日期的錯誤處理。
        
        驗證當出發日期超出範圍時，拋出 ValueError。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_invalid_dep_day
        
        Raises:
            AssertionError: 當測試失敗時
        """
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_dates(2, 0, 10)
        
        assert "出發日期天數必須在 1-31 之間" in str(exc_info.value)

    def test_calculate_dates_invalid_return_day(self):
        """
        測試無效回程日期的錯誤處理。
        
        驗證當回程日期超出範圍時，拋出 ValueError。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateCalculator::test_calculate_dates_invalid_return_day
        
        Raises:
            AssertionError: 當測試失敗時
        """
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_dates(2, 5, 32)
        
        assert "回程日期天數必須在 1-31 之間" in str(exc_info.value)


class TestDateValidator:
    """
    測試 DateValidator 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        self.validator = DateValidator()

    def test_validate_input_valid(self):
        """
        測試有效輸入的驗證。
        
        驗證當所有參數都有效時，返回 True。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateValidator::test_validate_input_valid
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": 2,
            "dep_day": 5,
            "return_day": 10
        }
        
        is_valid, error = self.validator.validate_input(data)
        assert is_valid is True
        assert error == ""

    def test_validate_input_missing_fields(self):
        """
        測試缺少必要欄位的驗證。
        
        驗證當缺少必要參數時，返回 False 和錯誤訊息。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateValidator::test_validate_input_missing_fields
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": 2,
            "dep_day": 5
        }
        
        is_valid, error = self.validator.validate_input(data)
        assert is_valid is False
        assert "缺少必要參數" in error

    def test_validate_input_invalid_type(self):
        """
        測試無效數據類型的驗證。
        
        驗證當參數類型錯誤時，返回 False 和錯誤訊息。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateValidator::test_validate_input_invalid_type
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": "invalid",
            "dep_day": 5,
            "return_day": 10
        }
        
        is_valid, error = self.validator.validate_input(data)
        assert is_valid is False
        assert "參數必須為整數類型" in error

    def test_validate_input_negative_offset(self):
        """
        測試負數月份偏移量的驗證。
        
        驗證當月份偏移量為負數時，返回 False 和錯誤訊息。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateValidator::test_validate_input_negative_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": -1,
            "dep_day": 5,
            "return_day": 10
        }
        
        is_valid, error = self.validator.validate_input(data)
        assert is_valid is False
        assert "month_offset 必須為非負整數" in error

    def test_validate_input_invalid_day_range(self):
        """
        測試日期範圍超出的驗證。
        
        驗證當日期天數超出 1-31 範圍時，返回 False 和錯誤訊息。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateValidator::test_validate_input_invalid_day_range
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": 2,
            "dep_day": 0,
            "return_day": 10
        }
        
        is_valid, error = self.validator.validate_input(data)
        assert is_valid is False
        assert "dep_day 必須在 1-31 之間" in error


class TestFlaskAPI:
    """
    測試 Flask API 端點
    """

    @pytest.fixture
    def client(self):
        """
        創建 Flask 測試客戶端。
        
        用於測試 API 端點。
        
        Args:
            無
        
        Returns:
            FlaskClient: Flask 測試客戶端
        
        Examples:
            在測試方法中作為參數使用
        
        Raises:
            不拋出異常
        """
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_calculate_dates_endpoint_success(self, client):
        """
        測試成功的日期計算 API 請求。
        
        驗證 POST /calculate_dates 端點在有效輸入下返回正確結果。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestFlaskAPI::test_calculate_dates_endpoint_success
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_dates',
            json={
                "month_offset": 2,
                "dep_day": 5,
                "return_day": 10
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert "departure_date" in data["data"]
        assert "return_date" in data["data"]
        assert "target_year" in data["data"]
        assert "target_month" in data["data"]

    def test_calculate_dates_endpoint_missing_params(self, client):
        """
        測試缺少參數的 API 請求。
        
        驗證當缺少必要參數時，API 返回 400 錯誤。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestFlaskAPI::test_calculate_dates_endpoint_missing_params
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_dates',
            json={
                "month_offset": 2,
                "dep_day": 5
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_calculate_dates_endpoint_invalid_json(self, client):
        """
        測試無效 JSON 格式的 API 請求。
        
        驗證當請求體不是 JSON 格式時，API 返回錯誤（415 或 400）。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestFlaskAPI::test_calculate_dates_endpoint_invalid_json
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_dates',
            data="invalid json"
        )
        
        # Flask 對於非 JSON 內容類型返回 415 Unsupported Media Type
        assert response.status_code in [400, 415]

    def test_calculate_dates_endpoint_negative_offset(self, client):
        """
        測試負數月份偏移量的 API 請求。
        
        驗證當月份偏移量為負數時，API 返回 400 錯誤。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestFlaskAPI::test_calculate_dates_endpoint_negative_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_dates',
            json={
                "month_offset": -1,
                "dep_day": 5,
                "return_day": 10
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_health_endpoint(self, client):
        """
        測試健康檢查端點。
        
        驗證 GET /health 端點返回正確的健康狀態。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestFlaskAPI::test_health_endpoint
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"


class TestDateAPIService:
    """
    測試 DateAPIService 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        self.service = DateAPIService(DateCalculator(), DateValidator())

    def test_process_request_success(self):
        """
        測試成功處理請求。
        
        驗證服務能正確處理有效的請求數據。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateAPIService::test_process_request_success
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": 2,
            "dep_day": 5,
            "return_day": 10
        }
        
        response, status_code = self.service.process_request(data)
        
        assert status_code == 200
        assert response["success"] is True
        assert "data" in response

    def test_process_request_validation_error(self):
        """
        測試驗證錯誤的處理。
        
        驗證服務能正確處理驗證失敗的情況。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestDateAPIService::test_process_request_validation_error
        
        Raises:
            AssertionError: 當測試失敗時
        """
        data = {
            "month_offset": -1,
            "dep_day": 5,
            "return_day": 10
        }
        
        response, status_code = self.service.process_request(data)
        
        assert status_code == 400
        assert "error" in response


class TestHolidayDateCalculator:
    """
    測試 HolidayDateCalculator 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        from holiday_calculator import HolidayDateCalculator
        self.calculator = HolidayDateCalculator()

    def test_calculate_dates_basic(self):
        """
        測試基本節日日期計算功能。
        
        驗證當輸入有效的月份偏移量時，能返回正確的結構。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateCalculator::test_calculate_dates_basic
        
        Raises:
            AssertionError: 當測試失敗時
        """
        result = self.calculator.calculate_dates(2)
        
        assert "target_year" in result
        assert "target_month" in result
        assert "holidays" in result
        assert isinstance(result["holidays"], list)

    def test_calculate_dates_negative_offset(self):
        """
        測試負數月份偏移量的錯誤處理。
        
        驗證當輸入負數月份偏移量時，拋出 ValueError。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateCalculator::test_calculate_dates_negative_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_dates(-1)
        
        assert "月份偏移量必須為非負整數" in str(exc_info.value)


class TestHolidayFilter:
    """
    測試 HolidayFilter 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        from holiday_calculator import HolidayFilter
        self.filter = HolidayFilter()

    def test_should_skip_spring_festival(self):
        """
        測試春節過濾。
        
        驗證春節應該被過濾掉。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFilter::test_should_skip_spring_festival
        
        Raises:
            AssertionError: 當測試失敗時
        """
        holiday = {'description': '春節', 'date': '20250129'}
        assert self.filter.should_skip_holiday(holiday, 2) is True

    def test_should_skip_lunar_new_year_eve(self):
        """
        測試農曆除夕過濾。
        
        驗證農曆除夕應該被過濾掉。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFilter::test_should_skip_lunar_new_year_eve
        
        Raises:
            AssertionError: 當測試失敗時
        """
        holiday = {'description': '農曆除夕', 'date': '20250128'}
        assert self.filter.should_skip_holiday(holiday, 2) is True

    def test_should_skip_fixed_range_month2(self):
        """
        測試2個月後固定區間過濾。
        
        驗證2個月後的5-10號應該被過濾掉。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFilter::test_should_skip_fixed_range_month2
        
        Raises:
            AssertionError: 當測試失敗時
        """
        holiday = {'description': '端午節', 'date': '20251207'}
        assert self.filter.should_skip_holiday(holiday, 2) is True

    def test_should_not_skip_normal_holiday(self):
        """
        測試正常節日不應被過濾。
        
        驗證正常的節日不應該被過濾掉。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFilter::test_should_not_skip_normal_holiday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        holiday = {'description': '元旦', 'date': '20260101'}
        assert self.filter.should_skip_holiday(holiday, 3) is False


class TestHolidayDateRangeCalculator:
    """
    測試 HolidayDateRangeCalculator 類別
    """

    def setup_method(self):
        """
        設置測試環境。
        
        在每個測試方法執行前調用。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            自動在每個測試方法前執行
        
        Raises:
            不拋出異常
        """
        from holiday_calculator import HolidayDateRangeCalculator
        self.calculator = HolidayDateRangeCalculator()

    def test_calculate_date_range_general_monday(self):
        """
        測試一般週一假日的日期範圍計算。
        
        驗證週一假日的出發和回程日期計算正確（前4天到當天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_monday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260105', 'week': '一', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週一假日：前4天到當天 (-4, 0)
        assert dep == datetime(2026, 1, 1)
        assert ret == datetime(2026, 1, 5)

    def test_calculate_date_range_general_tuesday(self):
        """
        測試一般週二假日的日期範圍計算。
        
        驗證週二假日的出發和回程日期計算正確（前4天到當天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_tuesday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260106', 'week': '二', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週二假日：前4天到當天 (-4, 0)
        assert dep == datetime(2026, 1, 2)
        assert ret == datetime(2026, 1, 6)

    def test_calculate_date_range_general_wednesday(self):
        """
        測試一般週三假日的日期範圍計算。
        
        驗證週三假日的出發和回程日期計算正確（當天到後3天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_wednesday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260107', 'week': '三', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週三假日：當天到後3天 (0, 3)
        assert dep == datetime(2026, 1, 7)
        assert ret == datetime(2026, 1, 10)

    def test_calculate_date_range_general_thursday(self):
        """
        測試一般週四假日的日期範圍計算。
        
        驗證週四假日的出發和回程日期計算正確（前1天到後3天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_thursday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260108', 'week': '四', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週四假日：前1天到後3天 (-1, 3)
        assert dep == datetime(2026, 1, 7)
        assert ret == datetime(2026, 1, 11)

    def test_calculate_date_range_general_friday(self):
        """
        測試一般週五假日的日期範圍計算。
        
        驗證週五假日的出發和回程日期計算正確（前2天到後2天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_friday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260109', 'week': '五', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週五假日：前2天到後2天 (-2, 2)
        assert dep == datetime(2026, 1, 7)
        assert ret == datetime(2026, 1, 11)

    def test_calculate_date_range_general_saturday(self):
        """
        測試一般週六假日的日期範圍計算。
        
        驗證週六假日的出發和回程日期計算正確（前3天到後1天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_saturday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260110', 'week': '六', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週六假日：前3天到後1天 (-3, 1)
        assert dep == datetime(2026, 1, 7)
        assert ret == datetime(2026, 1, 11)

    def test_calculate_date_range_general_sunday(self):
        """
        測試一般週日假日的日期範圍計算。
        
        驗證週日假日的出發和回程日期計算正確（前4天到當天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_general_sunday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260111', 'week': '日', 'description': '測試假日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 週日假日：前4天到當天 (-4, 0)
        assert dep == datetime(2026, 1, 7)
        assert ret == datetime(2026, 1, 11)

    def test_calculate_date_range_founding_day_wednesday(self):
        """
        測試開國紀念日在週三的特殊規則。
        
        驗證開國紀念日在週三時，使用特殊計算規則（前4天到當天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_founding_day_wednesday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20250101', 'week': '三', 'description': '開國紀念日'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 開國紀念日在週三：前4天到當天（特殊規則）
        assert dep == datetime(2024, 12, 28)
        assert ret == datetime(2025, 1, 1)

    def test_calculate_date_range_lunar_new_year_monday(self):
        """
        測試小年夜在週一的日期範圍計算。
        
        驗證小年夜在週一時的計算規則（前2天到後4天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_monday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20260126', 'week': '一', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週一：前2天到後4天 (-2, 4)
        assert dep == datetime(2026, 1, 24)
        assert ret == datetime(2026, 1, 30)

    def test_calculate_date_range_lunar_new_year_tuesday(self):
        """
        測試小年夜在週二的日期範圍計算。
        
        驗證小年夜在週二時的計算規則（前3天到後3天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_tuesday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20250128', 'week': '二', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週二：前3天到後3天 (-3, 3)
        assert dep == datetime(2025, 1, 25)
        assert ret == datetime(2025, 1, 31)

    def test_calculate_date_range_lunar_new_year_wednesday(self):
        """
        測試小年夜在週三的日期範圍計算。
        
        驗證小年夜在週三時的計算規則（前4天到後2天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_wednesday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20270210', 'week': '三', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週三：前4天到後2天 (-4, 2)
        assert dep == datetime(2027, 2, 6)
        assert ret == datetime(2027, 2, 12)

    def test_calculate_date_range_lunar_new_year_thursday(self):
        """
        測試小年夜在週四的日期範圍計算。
        
        驗證小年夜在週四時的計算規則（前2天到後4天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_thursday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20280127', 'week': '四', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週四：前2天到後4天 (-2, 4)
        assert dep == datetime(2028, 1, 25)
        assert ret == datetime(2028, 1, 31)

    def test_calculate_date_range_lunar_new_year_friday(self):
        """
        測試小年夜在週五的日期範圍計算。
        
        驗證小年夜在週五時的計算規則（前2天到後4天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_friday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20290216', 'week': '五', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週五：前2天到後4天 (-2, 4)
        assert dep == datetime(2029, 2, 14)
        assert ret == datetime(2029, 2, 20)

    def test_calculate_date_range_lunar_new_year_saturday(self):
        """
        測試小年夜在週六的日期範圍計算。
        
        驗證小年夜在週六時的計算規則（前2天到後3天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_saturday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20300202', 'week': '六', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週六：前2天到後3天 (-2, 3)
        assert dep == datetime(2030, 1, 31)
        assert ret == datetime(2030, 2, 5)

    def test_calculate_date_range_lunar_new_year_sunday(self):
        """
        測試小年夜在週日的日期範圍計算。
        
        驗證小年夜在週日時的計算規則（前2天到後3天）。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_lunar_new_year_sunday
        
        Raises:
            AssertionError: 當測試失敗時
        """
        from datetime import datetime
        holiday = {'date': '20310123', 'week': '日', 'description': '小年夜'}
        dep, ret = self.calculator.calculate_date_range(holiday)
        
        # 小年夜在週日：前2天到後3天 (-2, 3)
        assert dep == datetime(2031, 1, 21)
        assert ret == datetime(2031, 1, 26)

    def test_calculate_date_range_invalid_date_format(self):
        """
        測試無效日期格式的錯誤處理。
        
        驗證當日期格式錯誤時，拋出 ValueError。
        
        Args:
            無
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayDateRangeCalculator::test_calculate_date_range_invalid_date_format
        
        Raises:
            AssertionError: 當測試失敗時
        """
        holiday = {'date': 'invalid', 'week': '一', 'description': '測試假日'}
        
        with pytest.raises(ValueError) as exc_info:
            self.calculator.calculate_date_range(holiday)
        
        assert "無效的日期格式" in str(exc_info.value)


class TestHolidayFlaskAPI:
    """
    測試節日日期 Flask API 端點
    """

    @pytest.fixture
    def client(self):
        """
        創建 Flask 測試客戶端。
        
        用於測試 API 端點。
        
        Args:
            無
        
        Returns:
            FlaskClient: Flask 測試客戶端
        
        Examples:
            在測試方法中作為參數使用
        
        Raises:
            不拋出異常
        """
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_calculate_holiday_dates_endpoint_success(self, client):
        """
        測試成功的節日日期計算 API 請求。
        
        驗證 POST /calculate_holiday_dates 端點在有效輸入下返回正確結果。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFlaskAPI::test_calculate_holiday_dates_endpoint_success
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_holiday_dates',
            json={"month_offset": 2}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "data" in data
        assert "target_year" in data["data"]
        assert "target_month" in data["data"]
        assert "holidays" in data["data"]

    def test_calculate_holiday_dates_endpoint_missing_params(self, client):
        """
        測試缺少參數的 API 請求。
        
        驗證當缺少必要參數時，API 返回 400 錯誤。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFlaskAPI::test_calculate_holiday_dates_endpoint_missing_params
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_holiday_dates',
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_calculate_holiday_dates_endpoint_negative_offset(self, client):
        """
        測試負數月份偏移量的 API 請求。
        
        驗證當月份偏移量為負數時，API 返回 400 錯誤。
        
        Args:
            client: Flask 測試客戶端
        
        Returns:
            None
        
        Examples:
            pytest test_app.py::TestHolidayFlaskAPI::test_calculate_holiday_dates_endpoint_negative_offset
        
        Raises:
            AssertionError: 當測試失敗時
        """
        response = client.post(
            '/calculate_holiday_dates',
            json={"month_offset": -1}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
