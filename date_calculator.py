"""
日期計算模組

此模組負責處理固定月份的日期計算邏輯。
"""

from datetime import datetime
import calendar
from typing import Dict
from interfaces import IFixedMonthDateCalculator, IDateValidator
from zoneinfo import ZoneInfo


class DateCalculator(IFixedMonthDateCalculator):
    """
    日期計算器類別
    
    負責根據月份偏移量和日期天數計算目標日期。
    """

    def calculate_dates(self, month_offset: int, dep_day: int, return_day: int) -> Dict[str, str]:
        """
        根據月份偏移量計算目標日期區間。
        
        Args:
            month_offset (int): 月份偏移量，表示從當前月份往後推幾個月
            dep_day (int): 出發日期的天數（1-31）
            return_day (int): 回程日期的天數（1-31）
        
        Returns:
            Dict[str, str]: 包含計算後日期的字典，格式為：
                {
                    "departure_date": "YYYY-MM-DD",
                    "return_date": "YYYY-MM-DD",
                    "target_year": YYYY,
                    "target_month": MM
                }
        
        Examples:
            >>> calculator = DateCalculator()
            >>> result = calculator.calculate_dates(2, 5, 10)
            >>> result
            {'departure_date': '2025-12-05', 'return_date': '2025-12-10', 'target_year': 2025, 'target_month': 12}
        
        Raises:
            ValueError: 當 month_offset 小於 0 時
            ValueError: 當 dep_day 或 return_day 不在 1-31 範圍內時
        """
        if month_offset < 0:
            raise ValueError(f"月份偏移量必須為非負整數，目前值為 {month_offset}")
        
        if not 1 <= dep_day <= 31:
            raise ValueError(f"出發日期天數必須在 1-31 之間，目前值為 {dep_day}")
        
        if not 1 <= return_day <= 31:
            raise ValueError(f"回程日期天數必須在 1-31 之間，目前值為 {return_day}")
        
        # 獲取當前日期
        current_date = datetime.now(ZoneInfo("Asia/Taipei"))
        target_year = current_date.year
        target_month = current_date.month + month_offset
        
        # 處理跨年情況
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # 獲取目標月份的天數
        days_in_month = calendar.monthrange(target_year, target_month)[1]
        
        # 確保日期不超過該月份的最大天數
        actual_dep_day = min(dep_day, days_in_month)
        actual_return_day = min(return_day, days_in_month)
        
        # 格式化日期字符串
        departure_date = f"{target_year}-{target_month:02d}-{actual_dep_day:02d}"
        return_date = f"{target_year}-{target_month:02d}-{actual_return_day:02d}"
        
        return {
            "departure_date": departure_date,
            "return_date": return_date,
            "target_year": target_year,
            "target_month": target_month
        }


class DateValidator(IDateValidator):
    """
    日期驗證器類別
    
    負責驗證輸入參數的有效性。
    """

    def validate_input(self, data: Dict) -> tuple[bool, str]:
        """
        驗證輸入數據的有效性。
        
        Args:
            data (Dict): 包含輸入數據的字典，應包含 month_offset、dep_day、return_day
        
        Returns:
            tuple[bool, str]: (是否有效, 錯誤訊息)，如果有效則錯誤訊息為空字符串
        
        Examples:
            >>> validator = DateValidator()
            >>> validator.validate_input({"month_offset": 2, "dep_day": 5, "return_day": 10})
            (True, '')
            >>> validator.validate_input({"month_offset": -1, "dep_day": 5, "return_day": 10})
            (False, '缺少必要參數：month_offset, dep_day, return_day')
        
        Raises:
            不拋出異常，返回驗證結果
        """
        required_fields = ["month_offset", "dep_day", "return_day"]
        
        # 檢查必要欄位
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"缺少必要參數：{', '.join(required_fields)}"
        
        # 檢查數據類型
        try:
            month_offset = int(data["month_offset"])
            dep_day = int(data["dep_day"])
            return_day = int(data["return_day"])
        except (ValueError, TypeError):
            return False, "參數必須為整數類型"
        
        # 檢查數值範圍
        if month_offset < 0:
            return False, "month_offset 必須為非負整數"
        
        if not 1 <= dep_day <= 31:
            return False, "dep_day 必須在 1-31 之間"
        
        if not 1 <= return_day <= 31:
            return False, "return_day 必須在 1-31 之間"
        
        return True, ""
