#!/usr/bin/env python3
"""
PaddleOCR 版本的 OCR 提取脚本
专为中文优化，识别质量远超 Tesseract
"""

import sys
from pathlib import Path
from paddleocr import PaddleOCR
import warnings

# 忽略 PaddlePaddle 的警告信息
warnings.filterwarnings('ignore')

def init_ocr(lang='ch'):
    """
    初始化 PaddleOCR

    Args:
        lang: 语言，'ch'=中文, 'en'=英文, 'japan'=日文等
    """
    ocr = PaddleOCR(lang=lang)
    return ocr

def ocr_image(ocr, img_path: Path) -> str:
    """
    对单张图片进行 OCR

    Returns:
        提取的文字（纯文本，不做分析）
    """
    result_list = ocr.predict(input=str(img_path))

    if not result_list or len(result_list) == 0:
        return ""

    # PaddleOCR 返回一个列表，取第一个结果
    result = result_list[0]

    # 提取识别的文字（rec_texts 字段）
    if hasattr(result, 'rec_texts') and result.rec_texts:
        return "\n".join(result.rec_texts).strip()
    elif isinstance(result, dict) and 'rec_texts' in result:
        return "\n".join(result['rec_texts']).strip()

    return ""

def main():
    if len(sys.argv) < 3:
        print("用法: python paddle_ocr_to_md.py <输入目录或文件...> <输出.md> [语言]")
        print("示例: python paddle_ocr_to_md.py ./images output.md ch")
        print("语言选项: ch=中文(默认), en=英文, japan=日文, korean=韩文等")
        sys.exit(1)

    # 解析参数
    *inputs, out_md = sys.argv[1:-1], sys.argv[-1]
    lang = 'ch'  # 默认中文

    # 检查最后一个参数是否为语言参数
    if len(sys.argv) >= 4 and not sys.argv[-1].endswith('.md'):
        lang = sys.argv[-1]
        out_md = sys.argv[-2]
        inputs = sys.argv[1:-2]

    # 收集图片文件
    img_files = []
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            img_files += sorted([
                x for x in p.rglob("*")
                if x.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"]
            ])
        else:
            img_files.append(p)

    if not img_files:
        raise SystemExit("未找到图片文件")

    print(f"初始化 PaddleOCR (语言: {lang})...")
    ocr = init_ocr(lang=lang)

    chunks = []
    total = len(img_files)
    print(f"开始处理 {total} 张图片...\n")

    for idx, f in enumerate(img_files, 1):
        print(f"[{idx}/{total}] 正在识别: {f.name}")
        try:
            text = ocr_image(ocr, f)
            chunks.append(text)
            # 显示前50个字符作为预览
            preview = text[:50].replace('\n', ' ') if text else "(无文字)"
            print(f"           → {preview}...")
        except Exception as e:
            print(f"           ✗ 错误: {e}")
            chunks.append(f"[识别失败: {f.name}]")

    # 生成 Markdown 文件
    md = ("\n\n>>>\n\n").join(chunks).strip()
    # 在开头和结尾添加指定行
    md = "<参照持仓文件格式和锚点，生成今日持仓文件>\n\n" + md + "\n\n<参照持仓文件格式和锚点，生成今日持仓文件>"
    Path(out_md).write_text(md, encoding='utf-8')

    print(f"\n✓ 完成！已保存到: {out_md}")
    print(f"  共识别 {total} 张图片")

if __name__ == "__main__":
    main()
