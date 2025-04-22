"""
main.py – Image‑Trim API  (FastAPI + YOLOv8)
---------------------------------------------
GET  /                  : health‑check
POST /trim-single/      : 1 枚トリミング → URL 返却
POST /batch-trim-zip/   : 複数枚 ZIP 返却
    └ query ?focus=full|upper|lower
---------------------------------------------
"""

import shutil, zipfile, uuid
from pathlib import Path
from typing import List, Tuple, Optional

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from PIL import Image, ImageOps, ImageChops
import pillow_avif
import numpy as np, requests
from ultralytics import YOLO
from io import BytesIO

# ----------------- 基本設定 -----------------
WIDTH, HEIGHT = 750, 900
OUT_DIR = Path("output"); OUT_DIR.mkdir(exist_ok=True)
MODEL_PATH = Path("yolov8n.pt")
FOCUS_OPTIONS = ("full", "upper", "lower")

if not MODEL_PATH.exists():
    url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    MODEL_PATH.write_bytes(requests.get(url).content)

yolo = YOLO(str(MODEL_PATH))

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)
app.mount("/output", StaticFiles(directory="output"), name="output")

# ----------------- Utility -----------------
def remove_uniform_border(img: Image.Image, tol: int = 5) -> Image.Image:
    bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, bg).convert("L")
    bbox = diff.point(lambda p: p > tol and 255).getbbox()
    return img.crop(bbox) if bbox else img

def detect_person(img: Image.Image, conf=0.5) -> Optional[Tuple[int, int, int, int]]:
    arr = np.array(img)
    best, score = None, 0
    for r in yolo(arr, conf=conf):
        for b in r.boxes:
            if b.cls.cpu().numpy()[0] == 0:
                s = b.conf.cpu().numpy()[0]
                if s > score:
                    best, score = tuple(map(int, b.xyxy.cpu().numpy()[0])), s
    return best

def adjust_box(box, w, h, focus: str):
    x1, y1, x2, y2 = box
    pad = int((y2 - y1) * 0.20)
    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
    x2, y2 = min(w, x2 + pad), min(h, y2 + pad)

    person_height = y2 - y1

    if focus == "upper":
        y2 = min(h, y1 + int(person_height * 0.7))
    elif focus == "lower":
        shift = int(person_height * 0.3)
        if y2 + shift <= h:
            y1, y2 = y1 + shift, y2 + shift

    # 🔷 頭上余白が多すぎる場合のトリミング
    top_padding = y1
    if top_padding > int(0.15 * h):
        diff = top_padding - int(0.05 * h)
        y1 = max(0, y1 - diff)

    # アスペクト比補正（3:4）
    cur_ratio, tgt_ratio = (x2 - x1) / (y2 - y1), 3 / 4
    if cur_ratio > tgt_ratio:
        cx = (x1 + x2) // 2
        new_w = int((y2 - y1) * tgt_ratio)
        x1, x2 = cx - new_w // 2, cx + new_w // 2
    else:
        new_h = int((x2 - x1) / tgt_ratio)
        y2 = min(h, y1 + new_h)

    return x1, y1, x2, y2

def resize(img):
    return ImageOps.fit(img, (WIDTH, HEIGHT), Image.LANCZOS)

def process(img: Image.Image, focus: str):
    box = detect_person(img)
    if not box:
        return None
    box = adjust_box(box, img.width, img.height, focus)
    out = img.crop(box)
    out = remove_uniform_border(out)
    return resize(out)

def save_temp(u: UploadFile):
    tmp = Path(f"{uuid.uuid4().hex}.png")
    with tmp.open("wb") as bf:
        shutil.copyfileobj(u.file, bf)
    return tmp

# ----------------- Endpoints -----------------
@app.post("/trim-single/")
async def trim_single(
        file: UploadFile = File(...),
        focus: str = Query("full", regex="^(full|upper|lower)$")
    ):
    tmp = save_temp(file)
    try:
        img = Image.open(tmp).convert("RGB")
    except Exception as e:
        tmp.unlink(missing_ok=True)
        return JSONResponse(400, {"error": str(e)})

    result = process(img, focus)
    if result is None:
        tmp.unlink(missing_ok=True)
        return JSONResponse(422, {"error": "person not detected"})

    out_path = OUT_DIR / f"trimmed_{tmp.stem}.png"
    result.save(out_path, optimize=True)
    tmp.unlink(missing_ok=True)
    return {"image_url": f"/output/{out_path.name}"}

@app.post("/batch-trim-zip/")
async def batch_trim_zip(
        files: List[UploadFile] = File(...),
        focus: str = Query("full", regex="^(full|upper|lower)$")
    ):
    zip_name = f"trimmed_{uuid.uuid4().hex}.zip"
    zip_path = OUT_DIR / zip_name

    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in files:
            tmp = save_temp(f)
            try:
                img = Image.open(tmp).convert("RGB")
            except Exception:
                tmp.unlink(); continue

            res = process(img, focus)
            if res is None:
                tmp.unlink(); continue

            out_img = OUT_DIR / f"trim_{tmp.stem}.png"
            res.save(out_img, optimize=True)
            zf.write(out_img, arcname=out_img.name)
            tmp.unlink(); out_img.unlink()

    return FileResponse(zip_path, filename=zip_name, media_type="application/zip")

@app.get("/")
async def root():
    return {"message": "✅ Image Trim API is running!"}

# ----------------- Local dev -----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)







