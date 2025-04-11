# ベースイメージ
FROM python:3.10-slim

# OpenCVなど必要な依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# アプリコードをコピー
COPY . .

# Pythonパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# EXPOSEは意図を示すだけでOK
EXPOSE 8080

# 🚨 ポートをShell展開できる形式に（ここが重要）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
