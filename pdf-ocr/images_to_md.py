#!/usr/bin/env python3
"""
图片目录 → Markdown（PP-OCRv5 mobile）

用法：
    python3 images_to_md.py <图片目录> <输出.md>

示例：
    python3 images_to_md.py 起卦秘籍_pages 起卦秘籍.md
"""

import os
import sys
import warnings
from pathlib import Path

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR

warnings.filterwarnings("ignore")


def init_ocr():
    return PaddleOCR(
        lang="ch",
        text_detection_model_name='PP-OCRv5_mobile_det',
        text_recognition_model_name='PP-OCRv5_mobile_rec',
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )


def ocr_image(ocr, img_path: Path) -> str:
    result_list = ocr.predict(input=str(img_path))
    if not result_list:
        return ""
    result = result_list[0]
    if hasattr(result, 'rec_texts') and result.rec_texts:
        return "\n".join(result.rec_texts).strip()
    if isinstance(result, dict) and 'rec_texts' in result:
        return "\n".join(result['rec_texts']).strip()
    return ""


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    img_dir = Path(sys.argv[1])
    out_md = Path(sys.argv[2])

    if not img_dir.exists():
        print(f"✗ 目录不存在: {img_dir}")
        sys.exit(1)

    img_files = sorted([
        f for f in img_dir.iterdir()
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
    ])
    total = len(img_files)
    if total == 0:
        print(f"✗ 目录中没有图片: {img_dir}")
        sys.exit(1)

    print(f"图片目录: {img_dir}  共 {total} 张\n")
    print("初始化 PaddleOCR（PP-OCRv5 mobile）...")
    ocr = init_ocr()

    chunks = []
    print(f"开始 OCR...\n")
    for idx, f in enumerate(img_files, 1):
        print(f"[{idx}/{total}] {f.name}", end="  ")
        try:
            text = ocr_image(ocr, f)
            preview = text[:40].replace("\n", " ") if text else "(无文字)"
            print(f"→ {preview}...")
            chunks.append(text)
        except Exception as e:
            print(f"✗ 错误: {e}")
            chunks.append(f"[识别失败: {f.name}]")

    md = "\n\n>>>\n\n".join(chunks).strip()
    out_md.write_text(md, encoding="utf-8")
    print(f"\n✓ 完成！已保存到: {out_md}  ({len(md)} 字)")


if __name__ == "__main__":
    main()
