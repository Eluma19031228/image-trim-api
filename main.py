from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageOps
import shutil
from ultralytics import YOLO
import numpy as np
import uuid

# --- 共通定数と初期化 ---
OUTPUT_WIDTH, OUTPUT_HEIGHT = 750, 900
OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(exist_ok=True)
model = YOLO("yolov8n.pt")

app = FastAPI()


# --- 共通処理 ---
def detect_person_box(img):
    results = model(img)
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        if len(boxes) > 0:
            largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            x1, y1, x2, y2 = map(int, largest_box)
            return x1, y1, x2, y2
    return None


def resize_with_padding(img):
    return ImageOps.fit(img, (OUTPUT_WIDTH, OUTPUT_HEIGHT), method=Image.LANCZOS, bleed=0.02)


def process_image(img: Image.Image) -> Image.Image:
    box = detect_person_box(img)
    if box:
        img = img.crop(box)
    return resize_with_padding(img)


# --- FastAPIエンドポイント ---
@app.post("/trim")
async def trim_image(file: UploadFile = File(...)):
    temp_path = Path(f"tmp_{uuid.uuid4().hex}.png")

    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(temp_path).convert("RGB")
    resized = process_image(img)

    output_path = OUTPUT_FOLDER / f"trimmed_{temp_path.stem}.png"
    resized.save(output_path)

    temp_path.unlink()  # 一時ファイル削除

    return FileResponse(output_path)


# --- 一括処理モード ---
if __name__ == "__main__":
    print("📁 一括処理モード起動中…")

    INPUT_FOLDER = Path("input")
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    for img_file in INPUT_FOLDER.glob("*.jpg"):
        print(f"🖼️ 処理中: {img_file.name}")
        img = Image.open(img_file).convert("RGB")
        result = process_image(img)
        output_path = OUTPUT_FOLDER / f"{img_file.stem}_trimmed.png"
        result.save(output_path)

    print("✅ 一括処理が完了しました。")

