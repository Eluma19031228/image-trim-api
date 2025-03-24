from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from PIL import Image, ImageOps
import numpy as np
from ultralytics import YOLO
import uuid

app = FastAPI()

# モデルロード
model = YOLO("yolov8n.pt")

# 出力設定
OUTPUT_WIDTH, OUTPUT_HEIGHT = 750, 900
OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(exist_ok=True)

# 人物検出
def detect_person_box(img):
    results = model(np.array(img))
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        if len(boxes) > 0:
            largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            x1, y1, x2, y2 = map(int, largest_box)
            return x1, y1, x2, y2
    return None

# リサイズ処理
def resize_with_padding(img):
    return ImageOps.fit(img, (OUTPUT_WIDTH, OUTPUT_HEIGHT), method=Image.LANCZOS, bleed=0.02)

@app.post("/trim/")
async def trim_image(file: UploadFile = File(...)):
    # 一時保存
    temp_path = Path("temp") / f"{uuid.uuid4()}.png"
    temp_path.parent.mkdir(exist_ok=True)
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img = Image.open(temp_path).convert("RGB")
    box = detect_person_box(img)

    if box:
        cropped = img.crop(box)
        resized = resize_with_padding(cropped)
    else:
        resized = resize_with_padding(img)

    output_path = OUTPUT_FOLDER / f"trimmed_{temp_path.stem}.png"
    resized.save(output_path, "PNG", compress_level=6)

    return FileResponse(path=output_path, media_type="image/png", filename=output_path.name)
