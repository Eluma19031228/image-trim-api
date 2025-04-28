import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from pathlib import Path
from ultralytics import YOLO

# 画像フォルダの設定
INPUT_FOLDER = Path("C:/Users/tomok/OneDrive/デスクトップ/input")
OUTPUT_FOLDER = Path("C:/Users/tomok/OneDrive/デスクトップ/output")
OUTPUT_FOLDER.mkdir(exist_ok=True)  # 出力フォルダを作成

# 人体検出に特化したYOLOモデルをロード
yolo_model = YOLO("yolov8n.pt")  # yolov8m.pt なども試すと精度が上がる可能性あり

# 出力サイズ（アスペクト比 750×900px）
OUTPUT_WIDTH, OUTPUT_HEIGHT = 750, 900

# YOLOを使って人物のバウンディングボックスを取得
def detect_person_box(img):
    results = yolo_model(np.array(img))
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        if len(boxes) > 0:
            # 人物のバウンディングボックスを取得（最大のものを選択）
            largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            x1, y1, x2, y2 = map(int, largest_box)
            return x1, y1, x2, y2
    return None

# 画像のリサイズ（アスペクト比保持・不要な余白削除）
def resize_with_padding(img):
    img = ImageOps.fit(img, (OUTPUT_WIDTH, OUTPUT_HEIGHT), method=Image.LANCZOS, bleed=0.02)
    return img

# 画像のトリミング処理（人を基準に）
def process_image(img_path):
    img = Image.open(img_path).convert("RGB")

    # 人物の領域をYOLOで取得（元の画像に対して実施）
    person_box = detect_person_box(img)

    if person_box:
        x1, y1, x2, y2 = person_box

        # 適度なマージンを追加
        margin_x = int((x2 - x1) * 0.1)  # 横幅の10%をマージン
        margin_y = int((y2 - y1) * 0.1)  # 縦幅の10%をマージン
        x1, y1, x2, y2 = (
            max(0, x1 - margin_x),
            max(0, y1 - margin_y),
            min(img.width, x2 + margin_x),
            min(img.height, y2 + margin_y),
        )

        # 人の領域でトリミング
        img = img.crop((x1, y1, x2, y2))
    else:
        print(f"⚠️ {img_path.name} の人物領域が見つかりませんでした。")

    # アスペクト比を保持しつつ750×900にリサイズ（白い淵を防ぐ）
    img = resize_with_padding(img)

    # 保存
output_path = OUTPUT_FOLDER / f"{img_path.stem}_cropped.png"
img.save(output_path, "PNG", compress_level=6)
print(f"✅ 保存完了: {output_path}")


# 画像フォルダ内の全画像を処理
for img_file in INPUT_FOLDER.glob("*.jpg"):
    process_image(img_file)

print("🎉 すべての処理が完了しました!!!")

