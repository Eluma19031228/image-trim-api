"""
ローカル一括トリミングテスト
--------------------------------------------------
使い方:
    python localtest.py --focus upper     # トップス中心
    python localtest.py --focus lower     # スカート・パンツ中心
    python localtest.py                   # デフォルト(full)
--------------------------------------------------
input/  フォルダ内の画像をすべて処理し、
output/ に PNG で保存します。
"""

from pathlib import Path
import argparse, numpy as np, pillow_avif             # AVIF対応
from PIL import Image, ImageOps, ImageChops
from ultralytics import YOLO

# ---------- 設定 ----------
WIDTH, HEIGHT   = 750, 900
IN_DIR          = Path("input")
OUT_DIR         = Path("output")
MODEL_PATH      = Path("yolov8n.pt")
FOCUS_OPTIONS   = ("full", "upper", "lower")

model = YOLO(str(MODEL_PATH))

# ---------- ユーティリティ ----------
def remove_uniform_border(img: Image.Image, tolerance: int = 5) -> Image.Image:
    """画像の四辺にある単一色に近い帯を自動で切り取る"""
    bg   = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, bg).convert("L")
    bbox = diff.point(lambda p: p > tolerance and 255).getbbox()
    return img.crop(bbox) if bbox else img

def detect_person(img: Image.Image, conf=0.5):
    arr = np.array(img)
    results = model(arr, conf=conf)
    best, score = None, 0
    for r in results:
        for b in r.boxes:
            if b.cls.cpu().numpy()[0] == 0:            # class 0 = person
                s = b.conf.cpu().numpy()[0]
                if s > score:
                    best  = tuple(map(int, b.xyxy.cpu().numpy()[0]))
                    score = s
    return best

def adjust_box(box, w, h, focus):
    x1, y1, x2, y2 = box
    pad    = int((y2 - y1) * .20)                      # 20 % 余白
    x1, y1 = max(0, x1-pad), max(0, y1-pad)
    x2, y2 = min(w, x2+pad), min(h, y2+pad)

    if focus == "upper":                               # 上半身を強調
        y2 = y1 + int((y2 - y1) * .65)
    elif focus == "lower":                             # 下半身を強調（ただし顔は含む）
        shift = int((y2 - y1) * .25)
        if y2 + shift <= h:
            y1, y2 = y1 + shift, y2 + shift

    # アスペクト 3:4 に調整
    cur = (x2-x1)/(y2-y1)
    tgt = 3/4
    if cur > tgt:
        cx = (x1+x2)//2
        w_new = int((y2-y1)*tgt)
        x1, x2 = cx - w_new//2, cx + w_new//2
    else:
        h_new = int((x2-x1)/tgt)
        y2    = min(h, y1 + h_new)
    return x1, y1, x2, y2

def resize(img):                                      # 高画質リサイズ
    return ImageOps.fit(img, (WIDTH, HEIGHT), Image.LANCZOS)

# ---------- メイン処理 ----------
def process(img_path: Path, focus: str):
    try:
        img = Image.open(img_path).convert("RGB")
    except Exception as e:
        print(f"❌ {img_path.name}: 読み込み失敗 -> {e}")
        return

    box = detect_person(img)
    if not box:
        print(f"⚠️ {img_path.name}: 人物検出できずスキップ")
        return

    box = adjust_box(box, img.width, img.height, focus)
    cropped = img.crop(box)
    cropped = remove_uniform_border(cropped)          # ←白帯除去
    result  = resize(cropped)

    out_path = OUT_DIR / f"trimmed_{img_path.stem}.png"
    result.save(out_path, optimize=True)
    print(f"✅ {img_path.name} → {out_path.name}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", default="full", choices=FOCUS_OPTIONS,
                        help="トリミングの重心 (full / upper / lower)")
    args = parser.parse_args()

    IN_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    imgs = [p for p in IN_DIR.iterdir() if p.suffix.lower() in
            (".jpg", ".jpeg", ".png", ".avif")]
    if not imgs:
        print("📂 input/ に画像がありません")
        return

    print(f"🔄 {len(imgs)} 枚を処理 (focus={args.focus})")
    for p in imgs:
        process(p, args.focus)

if __name__ == "__main__":
    main()
