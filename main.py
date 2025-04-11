import zipfile
import shutil
import uuid
import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps
import numpy as np
from ultralytics import YOLO

app = FastAPI()

# --- CORS設定（Next.jsなどからアクセス許可）---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番は ["https://your-frontend.vercel.app"] に限定可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 初期設定 ---
OUTPUT_WIDTH, OUTPUT_HEIGHT = 750, 900
OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

MODEL_PATH = Path("yolov8n.pt")

# --- モデル存在確認 & 自動ダウンロード（クラウド用）---
if not MODEL_PATH.exists():
    import requests
    url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    print(f"🔽 モデルをダウンロード中: {url}")
    with open(MODEL_PATH, "wb") as f:
        f.write(requests.get(url).content)
    print("✅ モデルのダウンロード完了")

model = YOLO(str(MODEL_PATH))

# --- 人物検出 ---
def detect_person_box(img):
    results = model(img)
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        if len(boxes) > 0:
            largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            x1, y1, x2, y2 = map(int, largest_box)
            return x1, y1, x2, y2
    return None

# --- リサイズ処理 ---
def resize_with_padding(img: Image.Image) -> Image.Image:
    return ImageOps.fit(img, (OUTPUT_WIDTH, OUTPUT_HEIGHT), method=Image.LANCZOS, bleed=0.02)

# --- 画像トリミング処理 ---
def process_image(img: Image.Image) -> Image.Image:
    box = detect_person_box(img)
    if box:
        img = img.crop(box)
    return resize_with_padding(img)

# --- APIエンドポイント：一括画像アップロード & トリミングZIP出力 ---
@app.post("/batch-trim-zip/")
async def batch_trim_zip(files: List[UploadFile] = File(...)):
    print(f"📥 受信ファイル数: {len(files)} 件")
    for f in files:
        print(f" - {f.filename}")

    zip_name = f"trimmed_images_{uuid.uuid4().hex}.zip"
    zip_path = OUTPUT_FOLDER / zip_name

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in files:
            temp_path = Path(f"{uuid.uuid4().hex}.png")
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            img = Image.open(temp_path).convert("RGB")
            resized = process_image(img)

            output_img_path = OUTPUT_FOLDER / f"trimmed_{temp_path.stem}.png"
            resized.save(output_img_path)
            zipf.write(output_img_path, arcname=output_img_path.name)

            temp_path.unlink(missing_ok=True)
            output_img_path.unlink(missing_ok=True)

    print(f"📦 ZIP生成完了: {zip_path}")
    return FileResponse(zip_path, filename=zip_name, media_type='application/zip')

# --- ヘルスチェック用 ---
@app.get("/")
async def root():
    return {"message": "✅ Image Trim API is running!"}

# --- ローカル実行時のエントリーポイント ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)



