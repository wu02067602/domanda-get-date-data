# 日期計算 API

這是一個基於 Flask 的日期計算 API，用於根據月份偏移量計算目標日期區間。

## 功能說明

此 API 提供日期計算功能，輸入月份偏移量和出發/回程日期的天數，自動計算目標月份的完整日期。

### 商業邏輯

1. 接收月份偏移量（從當前月份往後推）
2. 接收出發日期和回程日期的天數
3. 計算目標年份和月份（處理跨年情況）
4. 確保日期不超過目標月份的最大天數
5. 返回完整的日期字符串（YYYY-MM-DD 格式）

## API 端點

### 1. 計算固定月份日期區間

**端點：** `POST /calculate_dates`

**請求格式：**

```json
{
  "month_offset": 2,
  "dep_day": 5,
  "return_day": 10
}
```

**參數說明：**

- `month_offset` (int): 月份偏移量，表示從當前月份往後推幾個月（必須 >= 0）
- `dep_day` (int): 出發日期的天數（1-31）
- `return_day` (int): 回程日期的天數（1-31）

**成功響應（200）：**

```json
{
  "success": true,
  "data": {
    "departure_date": "2025-12-05",
    "return_date": "2025-12-10",
    "target_year": 2025,
    "target_month": 12
  }
}
```

**錯誤響應（400）：**

```json
{
  "error": "錯誤訊息"
}
```

### 2. 計算節日日期區間

**端點：** `POST /calculate_holiday_dates`

**請求格式：**

```json
{
  "month_offset": 2
}
```

**參數說明：**

- `month_offset` (int): 月份偏移量，表示從當前月份往後推幾個月（必須 >= 0）

**成功響應（200）：**

```json
{
  "success": true,
  "data": {
    "target_year": 2025,
    "target_month": 12,
    "holidays": [
      {
        "holiday_name": "行憲紀念日",
        "holiday_date": "2025-12-25",
        "departure_date": "2025-12-21",
        "return_date": "2025-12-25",
        "weekday": "四"
      }
    ]
  }
}
```

**錯誤響應（400）：**

```json
{
  "error": "錯誤訊息"
}
```

**特點：**
- 自動從台灣政府 API 獲取節假日數據
- 根據星期幾自動計算最佳旅遊日期範圍
- 過濾掉春節、補假和與固定區間重疊的日期
- 佇列機制  
  - 避免併發問題，確保多個請求依序處理，防止全域變數競爭
  - 最大佇列長度：200 個待處理任務
  - 所有節日日期計算請求會依序執行
- 智能緩存機制
  - 自動緩存外部 API 響應，降低重複呼叫並提升效能
  - 以「年份 + 月份」作為緩存鍵值
  - 緩存資料結構：`{ target_year: { target_month: holiday_data } }`

### 3. 健康檢查

**端點：** `GET /health`

**響應（200）：**

```json
{
  "status": "healthy"
}
```

## 安裝與運行

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
python app.py
```

服務將在 `http://0.0.0.0:8080` 啟動。

### 3. 測試 API

**健康檢查：**

PowerShell:
```powershell
Invoke-RestMethod -Uri http://localhost:8080/health -Method Get
```

Bash/Linux:
```bash
curl -X GET http://localhost:8080/health
```

**測試固定月份 API：**

PowerShell:
```powershell
$body = @{month_offset=2; dep_day=5; return_day=10} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/calculate_dates -Method Post -Body $body -ContentType 'application/json' | ConvertTo-Json -Depth 10
```

Bash/Linux:
```bash
curl -X POST http://localhost:8080/calculate_dates \
  -H "Content-Type: application/json" \
  -d '{"month_offset": 2, "dep_day": 5, "return_day": 10}'
```

**測試節日 API：**

PowerShell:
```powershell
$body = @{month_offset=2} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8080/calculate_holiday_dates -Method Post -Body $body -ContentType 'application/json' | ConvertTo-Json -Depth 10
```

Bash/Linux:
```bash
curl -X POST http://localhost:8080/calculate_holiday_dates \
  -H "Content-Type: application/json" \
  -d '{"month_offset": 2}'
```

## 運行測試

```bash
pytest test_app.py -v
```

## 檔案結構

```
DateAPI/
├── app.py                          # Flask 應用程式主檔案（包含佇列機制）
├── date_calculator.py              # 固定月份日期計算實現
├── holiday_calculator.py           # 節日日期計算實現（包含緩存機制）
├── interfaces.py                   # 抽象接口定義（遵循 DIP & ISP）
├── requirements.txt                # Python 依賴套件
├── README.md                       # 專案說明文件
├── test_app.py                     # 單元測試（44 個測試用例）
├── Dockerfile                      # Docker 容器配置
└── cloudbuild.yaml                 # Cloud Build 配置
```

## 範例使用場景

此 API 適用於航班搜索系統，可以根據固定的月份偏移量和日期天數，動態生成爬蟲任務的實際日期。

例如：
- 輸入：2 個月後的 5 號出發，10 號回程
- 輸出：實際的日期字符串，用於航班搜索

## 錯誤處理

API 會驗證以下情況並返回相應錯誤：

1. 缺少必要參數
2. 參數類型錯誤
3. 月份偏移量為負數
4. 日期天數超出範圍（1-31）
