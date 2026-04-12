# 使用官方 Python 輕量版作為基礎影像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴項目 (用於圖像處理相關套件可能需要的函式庫)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt 並安裝 Python 套件 (利用 Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製其餘程式碼 (排除 .dockerignore 中指定的項目)
COPY . .

# 確保 backend 是一個可識別的 package
RUN touch backend/__init__.py

# 建立上傳目錄
RUN mkdir -p uploads

# 開放 API 服務埠號
EXPOSE 13984

# 使用 uvicorn 啟動服務
# 注意：使用 backend.main:app 形式，並指定 host 與 port
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "13984"]
