#!/usr/bin/env python3
"""
PDF 切页 → PNG 图片

用法：
    python3 pdf_to_images.py <input.pdf> [--dpi 200] [--out-dir ./pages] [--pages 1-10]

参数：
    input.pdf      输入 PDF 文件路径
    --dpi N        渲染分辨率，默认 200
    --out-dir DIR  输出目录，默认 <pdf名称>_pages/
    --pages A-B    只切指定页范围

示例：
    python3 pdf_to_images.py 起卦秘籍.pdf
    python3 pdf_to_images.py 起卦秘籍.pdf --dpi 300 --pages 1-10
"""

import sys
import warnings
from pathlib import Path

import fitz  # pymupdf

warnings.filterwarnings("ignore")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    dpi = 200
    out_dir = None
    page_range_str = None

    if "--dpi" in args:
        idx = args.index("--dpi")
        dpi = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if "--out-dir" in args:
        idx = args.index("--out-dir")
        out_dir = Path(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if "--pages" in args:
        idx = args.index("--pages")
        page_range_str = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    pdf_path = Path(args[0])
    if not pdf_path.exists():
        print(f"✗ 文件不存在: {pdf_path}")
        sys.exit(1)

    if out_dir is None:
        out_dir = pdf_path.parent / f"{pdf_path.stem}_pages"

    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    total = len(doc)

    if page_range_str:
        parts = page_range_str.split("-")
        start = int(parts[0]) - 1
        end = int(parts[1])
    else:
        start, end = 0, total

    print(f"PDF: {pdf_path.name}  总页数: {total}  处理范围: {start+1}~{end}  DPI: {dpi}")
    print(f"输出目录: {out_dir}\n")

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    count = end - start

    for i in range(start, end):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)
        img_path = out_dir / f"page_{i+1:04d}.png"
        pix.save(str(img_path))

        done = i - start + 1
        if done % 20 == 0 or done == count:
            print(f"  {done}/{count} 页")

    doc.close()
    print(f"\n✓ 完成！共 {count} 张图片保存到: {out_dir}")


if __name__ == "__main__":
    main()
