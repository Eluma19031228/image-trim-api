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

# Railway用にポートを明示
ENV PORT=8080
EXPOSE 8080

# 起動コマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]