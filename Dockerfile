# ベースイメージ
FROM python:3.10-slim

# 必要ライブラリをインストール（OpenCVがGL依存する）
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# アプリケーションのコードと依存ファイルをコピー
COPY . .

# パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# EXPOSE（意図の表明）
EXPOSE 8080

# CMD：PORT環境変数を展開して起動（Railway推奨）
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
