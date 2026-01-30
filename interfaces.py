"""
接口定義模組

定義抽象基類，遵循依賴反轉原則（DIP）和接口隔離原則（ISP）。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IDateCalculator(ABC):
    """
    日期計算器基礎接口
    
    定義日期計算的抽象接口，遵循依賴反轉原則。
    """

    @abstractmethod
    def calculate_dates(self, **kwargs) -> Dict[str, Any]:
        """
        計算日期。
        
        Args:
            **kwargs: 計算所需的參數，具體參數由實現類別定義
        
        Returns:
            Dict[str, Any]: 包含計算後日期的字典
        
        Examples:
            由具體實現類別提供
        
        Raises:
            ValueError: 當參數無效時
        """
        pass


class IFixedMonthDateCalculator(IDateCalculator):
    """
    固定月份日期計算器接口
    
    用於固定月份日期計算的專用接口，遵循接口隔離原則。
    """

    @abstractmethod
    def calculate_dates(self, month_offset: int, dep_day: int, return_day: int) -> Dict[str, str]:
        """
        根據月份偏移量和天數計算目標日期區間。
        
        Args:
            month_offset (int): 月份偏移量
            dep_day (int): 出發日期的天數
            return_day (int): 回程日期的天數
        
        Returns:
            Dict[str, str]: 包含計算後日期的字典
        
        Examples:
            由具體實現類別提供
        
        Raises:
            ValueError: 當參數無效時
        """
        pass


class IHolidayDateCalculator(IDateCalculator):
    """
    節日日期計算器接口
    
    用於節日日期計算的專用接口，遵循接口隔離原則。
    """

    @abstractmethod
    def calculate_dates(self, month_offset: int) -> Dict[str, Any]:
        """
        根據月份偏移量計算節假日日期區間。
        
        Args:
            month_offset (int): 月份偏移量
        
        Returns:
            Dict[str, Any]: 包含節假日日期列表的字典
        
        Examples:
            由具體實現類別提供
        
        Raises:
            ValueError: 當參數無效時
        """
        pass


class IDateValidator(ABC):
    """
    日期驗證器接口
    
    定義輸入驗證的抽象接口。
    """

    @abstractmethod
    def validate_input(self, data: Dict) -> tuple[bool, str]:
        """
        驗證輸入數據的有效性。
        
        Args:
            data (Dict): 輸入數據
        
        Returns:
            tuple[bool, str]: (是否有效, 錯誤訊息)
        
        Examples:
            由具體實現類別提供
        
        Raises:
            不拋出異常
        """
        pass
