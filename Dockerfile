# ベースイメージ：OpenCV動作に必要なGLライブラリを含むDebianベース
FROM python:3.10-slim

# OpenCVが必要とするライブラリをインストール
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# ローカルのコードと依存ファイルをコピー
COPY . .

# 依存パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# Railway用にポートを明示（環境変数として）
ENV PORT=8080
EXPOSE 8080

# CMDは $PORT を使って柔軟に対応（Railway推奨）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
