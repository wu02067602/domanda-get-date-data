"""
Temp Feature Blueprint - 可插拔的護照 OCR API 模組

此模組提供 YOLO + PaddleOCR 的護照欄位辨識功能。
統一掛載在 /temp/* 路徑下，不干擾既有 API。
"""

from flask import Blueprint

# 建立 Blueprint 實例
bp = Blueprint('temp_feature', __name__, url_prefix='/temp')

# 匯入路由（必須在 Blueprint 建立之後）
from . import routes  # noqa: F401, E402
