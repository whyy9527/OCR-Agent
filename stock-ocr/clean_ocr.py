#!/usr/bin/env python3
"""
OCR 噪声清理模块（DeepSeek）

对基金 APP 截图 OCR 后的原始文本做噪声清理。
每个 chunk 发给 DeepSeek，返回去噪后的纯文本（不做结构化）。
清理后进行数据校验。

单独使用：
    python3 clean_ocr.py <输入.md> [输出.md]
    # 输出.md 省略时覆盖输入文件

作为模块导入：
    from clean_ocr import clean_chunk   # 清理单个 chunk
    from clean_ocr import clean_md      # 清理整个 md（含 >>> 分隔）

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
你是一个 OCR 结果噪声清理工具。下面是从手机基金 APP 截图中 OCR 提取的原始文本，里面混杂了噪声。

你的任务是去除噪声行，保留有效数据行。

严格规则：
1. 只能删除行，或者对行做极小的修正（见下）。绝对不能新增任何内容。
2. 任何数字、金额、百分比，必须从原文原样保留，禁止修改、推算、或"修正"数值。
3. 输出纯文本，不加任何 markdown 格式（不加 ** 标题、不加 * 列表、不加 --- 分隔线）。
4. 保持原文行的顺序。

需要删除的噪声：
- 状态栏残片：时间（如 14:07、14:081）、电量数字（如 94、93、92）、汉字残片（三、三小）、粘连残片（三94、三小92）
- 单独的符号或乱码：> < ^ ￥ L □ D ® S · : i 、- 0 夫 大 贝聘 1印 9 日.
- 消息角标数字：单独的 27
- UI 按钮：产品详情、产品详情>、晒收益、切换标的、查看收益、什么是专项账户、基金（单独一行作为页面标题时）
- 底部操作栏：赎回/转换、购买/定投、招财号、讨论区、卖出、买入、定投（单独一行时）、完投、赎回、卖卖出、定定投、买、定
- 业绩图标签行及其粘连变体：
  - 单独的 "业绩走势"、"收益明细" → 整行删除
  - "业绩走势收益明细"、"业绩走势 收益明细" → 整行删除
  - "收益明细 实时估值+X%" 或 "业绩走势：收益明细 实时估值+X%" → 只保留 "实时估值+X%" 部分
- 市场资讯/新闻标题（跨行断裂的新闻标题，如 "拆解公募基金四季报：藏在数据中的七大投" + 下一行 "资线索"）
- 图表 Y 轴刻度：连续出现的纯百分比行（如 9.00% / 6.00% / 3.00%），且前面没有紧跟指标名（本基金/均值/基准/指数名）
- 图表 X 轴日期：25.12.31、26.02.02 这种格式
- 账户页横幅/提醒语：按策略挑选收益潜力更大的偏股基金、您未持有积蓄型保险，配置锁定长期收益、类似的推荐或提醒横幅
- 单独的短数字残片：单独一行只有 -2 这种负号+1~2位整数
- 单独的 "说明：" 行
- 末尾时间戳：如 "2026年2月3日 16:55" 这种日期+时间格式
- 营销文案：如 "未配置，26年想省税第一波..."
- 功能入口：持仓透视、我的定投、交易记录、持仓检视
- 新闻标题：如 "2025年四季报出炉|易方达主动权益投资业绩亮眼"
- 解读（单独一行时）
- 银行卡尾号信息：银行卡尾号、尾号XXXX等

需要保留的数据（注意不要误删）：
- 基金名称、基金代码（6位数字）
- 金额、净值、成本价、份额等数值
- 昨日收益、持仓收益、持仓收益率
- 在途资金、可用份额、日涨幅、最新净值、持仓成本价
- 实时估值（如 实时估值+1.49%）
- 业绩指标值（紧跟指标名后面的百分比，如 "本基金" 后面的 -1.17%）
- N个进行中定投计划、N笔交易进行中
- 定投金额（如 定投10.00元）
- 该基金暂不能申购
- 总金额等账户信息

允许做的行内小修正：
- "金额（元）0" → "金额（元）"（去掉尾部多余的 0）
- "您已持有49天0" → "您已持有49天"（同上）
- "指数型-股票被动均值0" → "指数型-股票被动均值"（均值后尾 0）
- "业绩比较基准▼" → "业绩比较基准"（去掉 ▼）
- "195,921.06 >" → "195,921.06"（去掉行尾的 >）
- "· 股票型均值" → "股票型均值"（去掉前导 · 或 ●）
- 金额格式统一：
  - "279.411.6" → "279,411.60"（错误的点号分隔符改为逗号，补齐两位小数）
  - "52，696.57" → "52,696.57"（中文逗号改为英文逗号）
  - 任何金额中的中文逗号（，）都改为英文逗号（,）
  - 小数点后只有一位的金额补齐为两位（如 .6 → .60）

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
    cleaned = cleaned if cleaned else raw

    # 数据校验
    cleaned = validate_cleaned_text(cleaned)
    return cleaned


def validate_cleaned_text(text: str) -> str:
    """对清理后的文本进行数据校验和基本修正"""
    if not text.strip():
        return text

    lines = text.strip().split('\n')
    validated_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 基本校验规则
        # 1. 检查是否包含明显的OCR残片（单个字符或乱码）
        if len(line) == 1 and line in '> < ^ ￥ L □ D ® S · : i 、- 0 夫 大 贝聘 1印 9 日.':
            continue  # 跳过单个乱码字符

        # 2. 检查是否是纯时间格式（如14:07）
        if re.match(r'^\d{1,2}[:：]\d{2}$', line):
            continue

        # 3. 检查是否是纯百分比数字（图表Y轴刻度）
        if re.match(r'^-?\d+(\.\d{1,3})?%$', line) and len(lines) > 1:
            # 如果是连续百分比行，可能是图表刻度
            continue

        # 4. 检查是否是日期格式（如25.12.31）
        if re.match(r'^\d{2}\.\d{2}\.\d{2}$', line):
            continue

        # 5. 检查是否是银行卡尾号行
        if '银行卡尾号' in line or re.match(r'^尾号\d{4}$', line):
            continue

        # 6. 检查是否是短数字残片（1-3位数字，可能带负号）
        if re.match(r'^-?\d{1,3}$', line):
            continue

        validated_lines.append(line)

    # 如果校验后为空，返回原始第一行（避免完全丢失内容）
    if not validated_lines and lines:
        return lines[0].strip()

    return '\n'.join(validated_lines)


def clean_md(raw_md: str) -> str:
    """对整个 md 文本（含 >>> 分隔）做清理，保留首尾 <参照...> 行"""
    lines = raw_md.strip().split("\n")

    # 分离首尾标记行
    header = footer = ""
    if lines and lines[0].startswith("<"):
        header = lines[0]
        lines = lines[1:]
    if lines and lines[-1].startswith("<"):
        footer = lines[-1]
        lines = lines[:-1]

    body = "\n".join(lines).strip()
    chunks = [c.strip() for c in body.split(">>>") if c.strip()]
    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"  清理 chunk {i+1}/{len(chunks)}...")
        cleaned_chunks.append(clean_chunk(chunk))

    result = "\n\n>>>\n\n".join(cleaned_chunks)

    if header:
        result = header + "\n\n" + result
    if footer:
        result = result + "\n\n" + footer
    return result


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python3 clean_ocr.py <输入.md> [输出.md]")
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
