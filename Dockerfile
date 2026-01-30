# 使用官方 Python 運行時作為父鏡像
FROM python:3.10-slim

# 設置環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# 建立非 root 用戶以提高安全性
RUN useradd -m -u 1000 appuser

# 設置工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app.py .
COPY date_calculator.py .
COPY holiday_calculator.py .
COPY interfaces.py .

# 更改所有檔案的擁有者為 appuser
RUN chown -R appuser:appuser /app

# 切換到非 root 用戶
USER appuser

# Cloud Run 會注入 PORT 環境變數，我們需要在應用程式中使用它
# 暴露端口（供文檔記錄，Cloud Run 會自動處理端口映射）
EXPOSE 8080

# 健康檢查（可選，但建議加入）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=2)" || exit 1

# 啟動 Flask 應用
# 使用 gunicorn 作為生產環境 WSGI 伺服器（性能更好）
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
