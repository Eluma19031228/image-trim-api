import zipfile
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple, Optional
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
import pillow_avif  # AVIF形式を有効化
import numpy as np
from ultralytics import YOLO
import requests
from io import BytesIO

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 出力フォルダ設定
OUTPUT_WIDTH, OUTPUT_HEIGHT = 750, 900
OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# 静的ファイル公開
app.mount("/output", StaticFiles(directory="output"), name="output")

# YOLOv8 モデル準備
MODEL_PATH = Path("yolov8n.pt")
if not MODEL_PATH.exists():
    url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    with open(MODEL_PATH, "wb") as f:
        f.write(requests.get(url).content)

model = YOLO(str(MODEL_PATH))

# 人物検出
def detect_person_box(img: Image.Image) -> Optional[Tuple[int, int, int, int]]:
    img_np = np.array(img)
    results = model(img_np, conf=0.5)
    best_box = None
    best_score = 0
    for result in results:
        for box in result.boxes:
            if box.cls.cpu().numpy()[0] == 0:  # class 0 = person
                confidence = box.conf.cpu().numpy()[0]
                if confidence > best_score:
                    x1, y1, x2, y2 = map(int, box.xyxy.cpu().numpy()[0])
                    best_box = (x1, y1, x2, y2)
                    best_score = confidence
    return best_box

# トリミング領域調整
def optimize_crop_box(box: Tuple[int, int, int, int], img_width: int, img_height: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    height = y2 - y1
    padding = int(height * 0.2)
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img_width, x2 + padding)
    y2 = min(img_height, y2 + padding)

    current_ratio = (x2 - x1) / (y2 - y1)
    target_ratio = 3 / 4
    if current_ratio > target_ratio:
        center_x = (x1 + x2) // 2
        width = int((y2 - y1) * target_ratio)
        x1 = center_x - width // 2
        x2 = center_x + width // 2
    else:
        height = int((x2 - x1) / target_ratio)
        y2 = min(img_height, y1 + height)

    return (x1, y1, x2, y2)

# 高品質リサイズ
def resize_with_padding(img: Image.Image) -> Image.Image:
    return ImageOps.fit(img, (OUTPUT_WIDTH, OUTPUT_HEIGHT), method=Image.LANCZOS)

# メイン画像処理
def process_image(img: Image.Image) -> Image.Image:
    box = detect_person_box(img)
    if box:
        box = optimize_crop_box(box, img.width, img.height)
        img = img.crop(box)
    return resize_with_padding(img)

# --- 複数画像ZIPエンドポイント ---
@app.post("/batch-trim-zip/")
async def batch_trim_zip(files: List[UploadFile] = File(...)):
    zip_name = f"trimmed_images_{uuid.uuid4().hex}.zip"
    zip_path = OUTPUT_FOLDER / zip_name

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in files:
            temp_path = Path(f"{uuid.uuid4().hex}.png")
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            try:
                img = Image.open(temp_path).convert("RGB")
            except Exception as e:
                return JSONResponse(status_code=400, content={"error": f"{file.filename} 読み込み失敗: {str(e)}"})

            resized = process_image(img)
            output_img_path = OUTPUT_FOLDER / f"trimmed_{temp_path.stem}.png"
            resized.save(output_img_path, quality=95)
            zipf.write(output_img_path, arcname=output_img_path.name)
            temp_path.unlink(missing_ok=True)
            output_img_path.unlink(missing_ok=True)

    return FileResponse(zip_path, filename=zip_name, media_type="application/zip")

# --- 単一画像処理 ---
@app.post("/trim-single/")
async def trim_single(file: UploadFile = File(...)):
    temp_path = OUTPUT_FOLDER / f"temp_{uuid.uuid4().hex}.png"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        img = Image.open(temp_path).convert("RGB")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"読み込み失敗: {str(e)}"})
    resized = process_image(img)
    output_path = OUTPUT_FOLDER / f"trimmed_{temp_path.stem}.png"
    resized.save(output_path, quality=95)
    temp_path.unlink(missing_ok=True)
    return {"image_url": f"/output/{output_path.name}"}

# --- プレビュー ---
@app.post("/test-preview/")
async def test_preview(file: UploadFile = File(...)):
    temp_path = OUTPUT_FOLDER / f"preview_{uuid.uuid4().hex}.png"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        img = Image.open(temp_path).convert("RGB")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"読み込み失敗: {str(e)}"})
    result = process_image(img)
    result.save(temp_path, quality=95)
    return {"image_url": f"/output/{temp_path.name}"}

# --- サンプル画像 ---
@app.get("/test-sample/")
async def test_sample():
    sample_url = "https://example.com/sample-apparel.jpg"
    try:
        response = requests.get(sample_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        resized = process_image(img)
        output_path = OUTPUT_FOLDER / "sample_result.png"
        resized.save(output_path, quality=95)
        return {"image_url": "/output/sample_result.png"}
    except Exception as e:
        return {"error": str(e)}

# --- ヘルスチェック ---
@app.get("/")
async def root():
    return {"message": "✅ Image Trim API is running!"}

# --- ローカル起動 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)





