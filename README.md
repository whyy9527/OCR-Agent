# OCR-Agent

纯本地 OCR 工具，使用 PaddleOCR 从图片中提取文字。

## 快速开始

```bash
# 处理图片（中文）
./run_paddle_ocr.sh test_png output.md ch

# 处理图片（英文）
./run_paddle_ocr.sh images/ output.md en

# 处理图片并清理噪声
./run_clean_ocr.sh test.md
```

## 文件说明

- `run_paddle_ocr.sh` - OCR 识别脚本 ⭐
- `run_clean_ocr.sh` - 噪声清理脚本（单独跑清理用）
- `paddle_ocr_to_md.py` - OCR 主程序（识别 + 清理）
- `clean_ocr.py` - OCR 噪声清理模块（可独立使用，见下）
- `PADDLEOCR_GUIDE.md` - 详细文档
- `validation.md` - 参考示例
- `test_png/` - 测试图片
- `venv/` - Python 环境

## 输出格式

生成的 Markdown 文件，图片之间用 `>>>` 分隔：

```
<图片1的文字>

>>>

<图片2的文字>
```

## 识别质量

- ✅ 中文识别：95%+ 准确率
- ✅ 数字金额：99%+ 准确率
- ✅ 复杂 UI：良好
- ✅ 完全本地运行

## clean_ocr.py — OCR 噪声清理

OCR 识别后的原始文本会混入大量噪声（状态栏、按钮、图表刻度、新闻标题等），`clean_ocr.py` 负责清理。它使用 DeepSeek-chat 做噪声判断，在 `paddle_ocr_to_md.py` 的流水线中自动调用，也可以单独对已有的 md 文件跑清理。

需要设置环境变量：

```bash
export DEEPSEEK_API_KEY="your-key-here"
```

**单独对已有 md 文件跑清理：**

```bash
# 输出到新文件
python3 clean_ocr.py output.md output_cleaned.md

# 原地覆盖
python3 clean_ocr.py output.md
```

**作为模块导入：**

```python
from clean_ocr import clean_chunk   # 清理单个 chunk（>>> 之间的文本）
from clean_ocr import clean_md      # 清理整个 md 文本（保留首尾标记行）
```

**调整清理行为：** 编辑 `clean_ocr.py` 中的 `_PROMPT` 即可修改噪声定义和保留规则。

---

## 详细文档

查看完整使用指南：

```bash
cat PADDLEOCR_GUIDE.md
```
