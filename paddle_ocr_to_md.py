#!/usr/bin/env python3
"""
PaddleOCR 版本的 OCR 提取脚本
专为中文优化，识别质量远超 Tesseract
"""

import sys
from pathlib import Path
from paddleocr import PaddleOCR
import warnings
from datetime import datetime

from clean_ocr import clean_chunk

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
        print("用法: python paddle_ocr_to_md.py [--skip-clean] <输入目录或文件...> <输出.md> [语言]")
        print("示例: python paddle_ocr_to_md.py ./images output.md ch")
        print("      python paddle_ocr_to_md.py --skip-clean ./images output.md ch")
        print("语言选项: ch=中文(默认), en=英文, japan=日文, korean=韩文等")
        print("--skip-clean: 跳过清理步骤，直接输出原始 OCR 文本")
        sys.exit(1)

    # 解析参数
    args = sys.argv[1:]  # 去掉脚本名
    skip_clean = False

    # 检查是否包含 --skip-clean 标志
    if '--skip-clean' in args:
        skip_clean = True
        args = [a for a in args if a != '--skip-clean']

    if len(args) < 2:
        print("错误: 需要至少两个参数（输入和输出文件）")
        sys.exit(1)

    # 根据剩余参数数量解析
    out_md = args[-1]
    lang = 'ch'  # 默认中文

    # 检查最后一个参数是否为语言参数
    if len(args) >= 3 and not args[-1].endswith('.md'):
        lang = args[-1]
        out_md = args[-2]
        inputs = args[:-2]
    else:
        inputs = args[:-1]

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
    if skip_clean:
        print("注意: 已启用 --skip-clean，将跳过清理步骤")
    else:
        print("将使用 deepseek-reasoner 进行 OCR 文本清理")

    chunks = []
    total = len(img_files)
    print(f"开始处理 {total} 张图片...\n")

    for idx, f in enumerate(img_files, 1):
        print(f"[{idx}/{total}] 正在识别: {f.name}")
        try:
            text = ocr_image(ocr, f)
            preview = text[:50].replace('\n', ' ') if text else "(无文字)"
            print(f"           → {preview}...")

            if not skip_clean:
                text = clean_chunk(text)
            chunks.append(text)
        except Exception as e:
            print(f"           ✗ 错误: {e}")
            chunks.append(f"[识别失败: {f.name}]")

    # 生成 Markdown 文件
    md = ("\n\n>>>\n\n").join(chunks).strip()
    # 在开头和结尾添加指定行，使用实时日期
    today = datetime.now().strftime("%Y年%m月%d日")
    md = f"<参照持仓文件格式和锚点，生成{today}持仓文件>\n\n" + md + f"\n\n<参照持仓文件格式和锚点，生成{today}持仓文件>"
    Path(out_md).write_text(md, encoding='utf-8')

    print(f"\n✓ 完成！已保存到: {out_md}")
    print(f"  共识别 {total} 张图片")

if __name__ == "__main__":
    main()
