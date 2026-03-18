#!/usr/bin/env python3
"""
书籍 OCR 噪声清理模块（DeepSeek）

对扫描书籍 OCR 后的原始文本做噪声清理，去除页眉页脚、页码、扫描噪点等。
与 clean_ocr.py 完全独立，不影响原有持仓图片清洗逻辑。

单独使用：
    python3 clean_book_ocr.py <输入.md> [输出.md]

作为模块导入：
    from clean_book_ocr import clean_chunk   # 清理单个 chunk
    from clean_book_ocr import clean_md      # 清理整个 md（含 >>> 分隔）

环境变量：
    DEEPSEEK_API_KEY  (必须)
"""

import os
import sys
import re
from pathlib import Path
from openai import OpenAI

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

_BASE_URL = "https://api.deepseek.com/v1"
_MODEL = "deepseek-chat"

_PROMPT = """\
你是一个书籍 OCR 结果噪声清理工具。下面是从扫描版书籍 PDF 中 OCR 提取的原始文本。

你的任务是还原干净的正文内容，去除扫描/OCR 引入的噪声。

严格规则：
1. 只能删除明确的噪声行，或做极小的文字修正。绝对不能新增内容，不能改写句子。
2. 原文的措辞、语气、用词必须完整保留，不得"优化"或"润色"。
3. 输出纯文本，不加任何 markdown 格式（不加 ** 标题、不加 * 列表、不加 --- 分隔线）。
4. 保持原文行的顺序。
5. 段落之间保留空行，不要把多段合并成一段。

需要删除的噪声：
- 页码：单独一行的纯数字（如 1、12、123）
- 页眉/页脚：重复出现的书名、章节名、作者名（单独一行且内容极短）
- 扫描边缘噪点：单个字符或无意义符号（如 | ！ . , 、 — ～ ……单独成行）
- 装订线阴影产生的竖线或横线：如 "|||"、"---"、"___" 单独成行
- OCR 识别失败产生的乱码：如 "口口口"、"□□□"、连续问号 "???"
- 扫描时带入的水印或章戳文字（通常斜体、与正文无关）
- 重复识别的同一行（完全相同的相邻两行，保留一行）

允许做的行内小修正：
- 明显的 OCR 错字修正，仅限高置信度情况：
  - "0" 误识别为 "O"（在明显是数字的上下文中）
  - "l"（小写L）误识别为 "1"（数字1）
  - 全角数字/字母统一为半角（如 "１２３" → "123"）
- 段首多余空格可去除（OCR 常把缩进识别为多个空格）

需要完整保留的内容：
- 正文所有句子，包括引用、注释、括号内容
- 标题、小标题（即使很短，只要是正文的一部分）
- 专有名词、人名、书名
- 数字（年份、章节号、引用编号等）
- 对话、引文中的标点

以下是需要清理的原始文本：

{raw_text}
"""

# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("✗ 环境变量 DEEPSEEK_API_KEY 未设置")
        _client = OpenAI(api_key=key, base_url=_BASE_URL)
    return _client


def clean_chunk(raw: str) -> str:
    """对单个 OCR chunk 调 DeepSeek 做清理，返回去噪后的纯文本"""
    if not raw.strip():
        return raw

    client = _get_client()
    prompt = _PROMPT.format(raw_text=raw)

    resp = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    cleaned = resp.choices[0].message.content.strip()
    return cleaned if cleaned else raw


def clean_md(raw_md: str) -> str:
    """对整个 md 文本（含 >>> 分隔）做清理"""
    chunks = [c.strip() for c in raw_md.split(">>>") if c.strip()]
    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"  清理 chunk {i+1}/{len(chunks)}...")
        cleaned_chunks.append(clean_chunk(chunk))

    return "\n\n>>>\n\n".join(cleaned_chunks)


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python3 clean_book_ocr.py <输入.md> [输出.md]")
        print("  输出.md 省略时覆盖输入文件")
        print("  需要设置环境变量: DEEPSEEK_API_KEY")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path

    if not input_path.exists():
        print(f"✗ 文件不存在: {input_path}")
        sys.exit(1)

    raw = input_path.read_text(encoding="utf-8")
    orig_len = len(raw)

    print(f"开始清理: {input_path}")
    cleaned = clean_md(raw)
    output_path.write_text(cleaned, encoding="utf-8")

    print(f"✓ 清理完成")
    print(f"  原文: {orig_len} 字 → 清理后: {len(cleaned)} 字 (去除 {(1 - len(cleaned)/orig_len)*100:.1f}%)")
    if output_path != input_path:
        print(f"  输出: {output_path}")


if __name__ == "__main__":
    main()
