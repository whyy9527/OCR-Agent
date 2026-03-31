#!/usr/bin/env python3
"""
PDF 扫描版书籍转 Markdown

流程：PDF → 每页渲染为图片 → PaddleOCR（中文，PP-OCRv5 mobile）→ Markdown

用法：
    python3 pdf_to_md.py <input.pdf> <output.md> [--dpi 200]

参数：
    input.pdf      输入 PDF 文件路径
    output.md      输出 Markdown 文件路径
    --dpi N        渲染分辨率，默认 200（越高质量越好但越慢，推荐 150-300）
    --pages A-B    只处理指定页范围，如 --pages 1-10（用于测试）

示例：
    # 全量转换
    python3 pdf_to_md.py 起卦秘籍.pdf 起卦秘籍.md

    # 只测试前 10 页
    python3 pdf_to_md.py 起卦秘籍.pdf test.md --pages 1-10
"""

import sys
import tempfile
import shutil
import warnings
from pathlib import Path

import fitz  # pymupdf
from paddleocr import PaddleOCR

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# PDF → 图片
# ---------------------------------------------------------------------------

def pdf_to_images(pdf_path: Path, out_dir: Path, dpi: int, page_range: tuple) -> list[Path]:
    """将 PDF 每页渲染为 PNG，返回图片路径列表（按页序）"""
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    start, end = page_range  # 0-indexed, end exclusive

    mat = fitz.Matrix(dpi / 72, dpi / 72)
    images = []
    print(f"渲染 PDF 页面（{start+1}~{end} 页，共 {total} 页，DPI={dpi}）...")

    for i in range(start, end):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat)
        img_path = out_dir / f"page_{i+1:04d}.png"
        pix.save(str(img_path))
        images.append(img_path)
        if (i - start + 1) % 20 == 0 or i == end - 1:
            print(f"  已渲染 {i - start + 1}/{end - start} 页")

    doc.close()
    return images

# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def ocr_image(ocr: PaddleOCR, img_path: Path) -> str:
    """对单张图片做 OCR，返回识别文字"""
    result_list = ocr.predict(input=str(img_path))
    if not result_list:
        return ""
    result = result_list[0]
    if hasattr(result, "rec_texts") and result.rec_texts:
        return "\n".join(result.rec_texts).strip()
    if isinstance(result, dict) and "rec_texts" in result:
        return "\n".join(result["rec_texts"]).strip()
    return ""

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    # 解析参数
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    dpi = 200
    if "--dpi" in args:
        idx = args.index("--dpi")
        dpi = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    page_range_str = None
    if "--pages" in args:
        idx = args.index("--pages")
        page_range_str = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    pdf_path = Path(args[0])
    out_md = Path(args[1])

    if not pdf_path.exists():
        print(f"✗ 文件不存在: {pdf_path}")
        sys.exit(1)

    # 确定页范围
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()

    if page_range_str:
        parts = page_range_str.split("-")
        start = int(parts[0]) - 1  # 转 0-indexed
        end = int(parts[1])
    else:
        start, end = 0, total_pages

    print(f"PDF: {pdf_path.name}  总页数: {total_pages}  处理范围: {start+1}~{end}")

    # 创建临时目录存放图片
    tmp_dir = Path(tempfile.mkdtemp(prefix="pdf_ocr_"))
    try:
        # Step 1: 渲染图片
        images = pdf_to_images(pdf_path, tmp_dir, dpi, (start, end))

        # Step 2: OCR
        print(f"\n初始化 PaddleOCR（中文，PP-OCRv5 mobile）...")
        ocr = PaddleOCR(
            lang="ch",
            text_detection_model_name='PP-OCRv5_mobile_det',
            text_recognition_model_name='PP-OCRv5_mobile_rec',
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )


        chunks = []
        total = len(images)
        print(f"开始 OCR，共 {total} 张图片...\n")

        for idx, img_path in enumerate(images, 1):
            page_num = start + idx
            print(f"[{idx}/{total}] 第 {page_num} 页", end="  ")
            try:
                text = ocr_image(ocr, img_path)
                preview = text[:40].replace("\n", " ") if text else "(无文字)"
                print(f"→ {preview}...")

                chunks.append(text)
            except Exception as e:
                print(f"✗ 错误: {e}")
                chunks.append(f"[识别失败: 第 {page_num} 页]")

        # Step 3: 写入 Markdown
        md = "\n\n>>>\n\n".join(chunks).strip()
        out_md.write_text(md, encoding="utf-8")

        print(f"\n✓ 完成！已保存到: {out_md}")
        print(f"  处理页数: {total}  输出大小: {len(md)} 字")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
