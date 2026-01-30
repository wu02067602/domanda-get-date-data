"""
節日日期計算模組

此模組負責處理節日日期的計算邏輯。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import json
from interfaces import IHolidayDateCalculator
from zoneinfo import ZoneInfo


class HolidayDataCache:
    """
    節日數據緩存管理器
    
    負責管理節假日數據的緩存操作，遵循單一職責原則（SRP）。
    """
    # 類別級別的共享緩存，所有實例共用
    _shared_cache: Dict[int, Dict[int, List[Dict]]] = {}

    def __init__(self, cache_storage: Dict = None):
        """
        初始化緩存管理器。
        
        Args:
            cache_storage (Dict): 緩存儲存容器，預設使用類別級別的 _shared_cache。
        """
        self.cache_storage = cache_storage if cache_storage is not None else self._shared_cache

    def get_holiday_data_cache(self, target_year: int, target_month: int) -> List[Dict] | None:
        """
        從緩存中獲取指定年月的節假日資料。
        
        Args:
            target_year (int): 目標年份
            target_month (int): 目標月份（1-12）
        
        Returns:
            List[Dict] | None: 如果緩存中有資料則返回，否則返回 None
        
        Examples:
            >>> cache = HolidayDataCache()
            >>> result = cache.get_holiday_data_cache(2025, 1)
            >>> result is None or isinstance(result, list)
            True
        
        Raises:
            不拋出異常
        """
        if target_year in self.cache_storage:
            if target_month in self.cache_storage[target_year]:
                return self.cache_storage[target_year][target_month]
        return None

    def set_holiday_data_cache(self, target_year: int, target_month: int, data: List[Dict]) -> None:
        """
        將節假日資料儲存到緩存中。
        
        Args:
            target_year (int): 目標年份
            target_month (int): 目標月份（1-12）
            data (List[Dict]): 節假日資料列表
        
        Returns:
            None
        
        Examples:
            >>> cache = HolidayDataCache()
            >>> cache.set_holiday_data_cache(2025, 1, [])
        
        Raises:
            不拋出異常
        """
        if target_year not in self.cache_storage:
            self.cache_storage[target_year] = {}
        self.cache_storage[target_year][target_month] = data

    def has_holiday_data_cache(self, target_year: int, target_month: int) -> bool:
        """
        檢查緩存中是否存在指定年月的資料。
        
        Args:
            target_year (int): 目標年份
            target_month (int): 目標月份（1-12）
        
        Returns:
            bool: 如果存在則返回 True，否則返回 False
        
        Examples:
            >>> cache = HolidayDataCache()
            >>> cache.has_holiday_data_cache(2025, 1)
            False
        
        Raises:
            不拋出異常
        """
        return self.get_holiday_data_cache(target_year, target_month) is not None


class HolidayDataFetcher:
    """
    節日數據獲取器
    
    負責從外部 API 獲取台灣節假日數據。
    遵循單一職責原則（SRP），僅負責數據獲取，不處理緩存。
    """

    def __init__(self, cache: HolidayDataCache = None):
        """
        初始化節日數據獲取器。
        
        Args:
            cache (HolidayDataCache): 緩存管理器實例，用於依賴注入
        
        Returns:
            None
        
        Examples:
            >>> fetcher = HolidayDataFetcher()
        
        Raises:
            不拋出異常
        """
        self.cache = cache or HolidayDataCache()

    def fetch_taiwan_holidays(self, target_year: int, target_month: int) -> List[Dict]:
        """
        從外部 API 獲取指定年月的台灣節假日資料。
        優先從緩存讀取，若無緩存則調用外部 API 並儲存結果。
        
        Args:
            target_year (int): 目標年份
            target_month (int): 目標月份（1-12）
        
        Returns:
            List[Dict]: 該月份的節假日資料列表，每個字典包含：
                - date: 日期字符串（YYYYMMDD 格式）
                - description: 節日描述
                - week: 星期幾（一、二、三、四、五、六、日）
                - isHoliday: 是否為假日
        
        Examples:
            >>> fetcher = HolidayDataFetcher()
            >>> holidays = fetcher.fetch_taiwan_holidays(2025, 1)
            >>> len(holidays) >= 0
            True
        
        Raises:
            requests.RequestException: 當 API 請求失敗時
        """
        # 先檢查緩存
        cached_data = self.cache.get_holiday_data_cache(target_year, target_month)
        if cached_data is not None:
            return cached_data
        
        # 緩存中沒有資料，從外部 API 獲取
        url = f"https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{target_year}.json"
        holidays_data = []
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                year_data = response.content.decode('utf-8-sig')
                year_data = json.loads(year_data)
                
                # 只保留指定月份且有 description 的節假日
                for holiday in year_data:
                    if (holiday.get('isHoliday') and 
                        holiday.get('description') != '' and
                        holiday['date'].startswith(f"{target_year}{target_month:02d}")):
                        holidays_data.append(holiday)
                
                # 剔除補假
                holidays_data = HolidayDataFetcher._remove_compensatory_holidays(holidays_data)
                
                # 儲存到緩存
                self.cache.set_holiday_data_cache(target_year, target_month, holidays_data)
                
        except requests.RequestException as e:
            raise requests.RequestException(f"無法獲取 {target_year} 年 {target_month} 月節假日資料: {e}")
        
        return holidays_data

    @staticmethod
    def _remove_compensatory_holidays(holidays_data: List[Dict]) -> List[Dict]:
        """
        剔除 API 描述中補假的國定假日。
        
        如果資料中包含「補」這個字，則剔除。
        
        Args:
            holidays_data (List[Dict]): 節假日資料列表
        
        Returns:
            List[Dict]: 剔除補假後的節假日資料列表
        
        Examples:
            >>> data = [{'description': '元旦'}, {'description': '元旦補假'}]
            >>> result = HolidayDataFetcher._remove_compensatory_holidays(data)
            >>> len(result)
            1
        
        Raises:
            不拋出異常
        """
        return [holiday for holiday in holidays_data if '補' not in holiday.get('description', '')]


class HolidayDateRangeCalculator:
    """
    節日日期範圍計算器
    
    負責根據節假日的星期幾計算出發和回程日期。
    """

    @staticmethod
    def calculate_date_range(holiday: Dict) -> tuple[datetime, datetime]:
        """
        根據節假日和星期幾，返回需要的日期範圍。
        
        Args:
            holiday (Dict): 節假日資料，包含 date、week、description
        
        Returns:
            tuple[datetime, datetime]: (出發日期, 回程日期)
        
        Examples:
            >>> holiday = {'date': '20250101', 'week': '三', 'description': '開國紀念日'}
            >>> dep, ret = HolidayDateRangeCalculator.calculate_date_range(holiday)
            >>> isinstance(dep, datetime)
            True
        
        Raises:
            ValueError: 當日期格式無效時
        """
        # 解析日期
        date_str = holiday['date']
        try:
            holiday_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError as e:
            raise ValueError(f"無效的日期格式：{date_str}")
        
        weekday = holiday.get('week', '')
        description = holiday.get('description', '')
        
        # 根據不同情況設定爬取日期
        if '開國紀念日' in description and weekday == '三':
            # 開國紀念日落在週三的特殊規則
            crawl_dates = (holiday_date - timedelta(days=4), holiday_date)
        elif '小年夜' in description:
            # 春節規則（以小年夜為基準）
            crawl_dates = HolidayDateRangeCalculator._calculate_lunar_new_year_range(
                holiday_date, weekday
            )
        else:
            # 一般國定假日規則
            crawl_dates = HolidayDateRangeCalculator._calculate_general_holiday_range(
                holiday_date, weekday
            )
        
        return crawl_dates

    @staticmethod
    def _calculate_lunar_new_year_range(holiday_date: datetime, weekday: str) -> tuple[datetime, datetime]:
        """
        計算小年夜的日期範圍。
        
        Args:
            holiday_date (datetime): 小年夜日期
            weekday (str): 星期幾
        
        Returns:
            tuple[datetime, datetime]: (出發日期, 回程日期)
        
        Examples:
            >>> date = datetime(2025, 1, 28)
            >>> dep, ret = HolidayDateRangeCalculator._calculate_lunar_new_year_range(date, '二')
            >>> isinstance(dep, datetime)
            True
        
        Raises:
            不拋出異常
        """
        weekday_rules = {
            '一': (-2, 4),
            '二': (-3, 3),
            '三': (-4, 2),
            '四': (-2, 4),
            '五': (-2, 4),
            '六': (-2, 3),
            '日': (-2, 3)
        }
        
        days_before, days_after = weekday_rules.get(weekday, (-2, 4))
        return (
            holiday_date + timedelta(days=days_before),
            holiday_date + timedelta(days=days_after)
        )

    @staticmethod
    def _calculate_general_holiday_range(holiday_date: datetime, weekday: str) -> tuple[datetime, datetime]:
        """
        計算一般國定假日的日期範圍。
        
        Args:
            holiday_date (datetime): 假日日期
            weekday (str): 星期幾
        
        Returns:
            tuple[datetime, datetime]: (出發日期, 回程日期)
        
        Examples:
            >>> date = datetime(2025, 1, 1)
            >>> dep, ret = HolidayDateRangeCalculator._calculate_general_holiday_range(date, '三')
            >>> isinstance(dep, datetime)
            True
        
        Raises:
            不拋出異常
        """
        weekday_rules = {
            '一': (-4, 0),
            '二': (-4, 0),
            '三': (0, 3),
            '四': (-1, 3),
            '五': (-2, 2),
            '六': (-3, 1),
            '日': (-4, 0)
        }
        
        days_before, days_after = weekday_rules.get(weekday, (-4, 0))
        return (
            holiday_date + timedelta(days=days_before),
            holiday_date + timedelta(days=days_after)
        )


class HolidayFilter:
    """
    節日過濾器
    
    負責過濾掉不需要處理的節日。
    """

    @staticmethod
    def should_skip_holiday(holiday: Dict, month_offset: int) -> bool:
        """
        判斷是否應該跳過此節日。
        
        跳過規則：
        1. 春節和農曆除夕
        2. 與固定月份區間重疊的日期（2個月的5-10號、6個月的24-28號）
        
        Args:
            holiday (Dict): 節假日資料
            month_offset (int): 月份偏移量
        
        Returns:
            bool: 是否應該跳過此節日
        
        Examples:
            >>> holiday = {'description': '春節', 'date': '20250129'}
            >>> HolidayFilter.should_skip_holiday(holiday, 2)
            True
        
        Raises:
            ValueError: 當日期格式無效時
        """
        description = holiday.get('description', '')
        
        # 跳過春節和農曆除夕
        if any(keyword in description for keyword in ['春節', '農曆除夕']):
            return True
        
        # 跳過與固定區間重疊的日期
        date_str = holiday.get('date', '')
        try:
            holiday_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError as e:
            raise ValueError(f"無效的日期格式：{date_str}")
        
        day = holiday_date.day
        
        # 2個月後的5-10號
        if month_offset == 2 and 5 <= day <= 10:
            return True
        # 6個月後的24-28號
        elif month_offset == 6 and 24 <= day <= 28:
            return True
        
        return False


class HolidayDateCalculator(IHolidayDateCalculator):
    """
    節日日期計算器
    
    負責計算指定月份偏移量的所有節假日日期範圍。
    """

    def __init__(self, 
                 data_fetcher: HolidayDataFetcher = None,
                 range_calculator: HolidayDateRangeCalculator = None,
                 holiday_filter: HolidayFilter = None):
        """
        初始化節日日期計算器。
        
        Args:
            data_fetcher (HolidayDataFetcher): 節日數據獲取器
            range_calculator (HolidayDateRangeCalculator): 日期範圍計算器
            holiday_filter (HolidayFilter): 節日過濾器
        
        Returns:
            None
        
        Examples:
            >>> calculator = HolidayDateCalculator()
            >>> isinstance(calculator, IHolidayDateCalculator)
            True
        
        Raises:
            不拋出異常
        """
        self.data_fetcher = data_fetcher or HolidayDataFetcher()
        self.range_calculator = range_calculator or HolidayDateRangeCalculator()
        self.holiday_filter = holiday_filter or HolidayFilter()

    def calculate_dates(self, month_offset: int) -> Dict[str, Any]:
        """
        計算指定月份偏移量的所有節假日日期範圍。
        
        Args:
            month_offset (int): 月份偏移量，表示從當前月份往後推幾個月
        
        Returns:
            Dict: 包含節假日日期列表的字典，格式為：
                {
                    "target_year": YYYY,
                    "target_month": MM,
                    "holidays": [
                        {
                            "holiday_name": "節日名稱",
                            "holiday_date": "YYYY-MM-DD",
                            "departure_date": "YYYY-MM-DD",
                            "return_date": "YYYY-MM-DD",
                            "weekday": "星期幾"
                        },
                        ...
                    ]
                }
        
        Examples:
            >>> calculator = HolidayDateCalculator()
            >>> # 注意：這個測試可能因為實際節假日數據而變化
            >>> result = calculator.calculate_dates(2)
            >>> "target_year" in result
            True
        
        Raises:
            ValueError: 當 month_offset 小於 0 時
            requests.RequestException: 當無法獲取節假日數據時
        """
        if month_offset < 0:
            raise ValueError(f"月份偏移量必須為非負整數，目前值為 {month_offset}")
        
        # 計算目標年月
        current_date = datetime.now(ZoneInfo("Asia/Taipei"))
        target_year = current_date.year
        target_month = current_date.month + month_offset
        
        # 處理跨年情況
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # 獲取節假日數據
        try:
            holidays_data = self.data_fetcher.fetch_taiwan_holidays(target_year, target_month)
        except requests.RequestException as e:
            raise requests.RequestException(f"獲取節假日數據失敗：{e}")
        
        # 處理每個節假日
        holiday_list = []
        for holiday in holidays_data:
            # 檢查是否應該跳過
            if not holiday.get('description'):
                continue
            if self.holiday_filter.should_skip_holiday(holiday, month_offset):
                continue
            
            # 計算日期範圍
            try:
                dep_date, ret_date = self.range_calculator.calculate_date_range(holiday)
            except ValueError as e:
                continue  # 跳過格式錯誤的日期
            
            holiday_list.append({
                "holiday_name": holiday.get('description', ''),
                "holiday_date": datetime.strptime(holiday['date'], "%Y%m%d").strftime("%Y-%m-%d"),
                "departure_date": dep_date.strftime("%Y-%m-%d"),
                "return_date": ret_date.strftime("%Y-%m-%d"),
                "weekday": holiday.get('week', '')
            })
        
        return {
            "target_year": target_year,
            "target_month": target_month,
            "holidays": holiday_list
        }
