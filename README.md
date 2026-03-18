# OCR-Agent

纯本地 OCR 工具集，支持两类场景：

| 目录 | 场景 | 说明 |
|------|------|------|
| `stock-ocr/` | 手机基金 APP 截图 | PaddleOCR + DeepSeek 持仓噪声清洗 |
| `pdf-ocr/` | 扫描版 PDF 书籍 | PDF→图片→PaddleOCR + DeepSeek 书籍噪声清洗 |

共用同一个 `venv/` 环境。

---

## 快速开始

### stock-ocr — 基金截图识别

截图按券商分两个子目录存放：

| 目录 | 来源 |
|------|------|
| `stock-ocr/images/cmb/` | 招商银行 |
| `stock-ocr/images/jd/`  | 京东金融 |

```bash
cd stock-ocr

# 识别全部截图（自动按招商银行/京东金融分组，输出含 === 招商银行 === / === 京东金融 === 标题）
./run_paddle_ocr.sh images output_all.md ch

# 单独识别招商银行截图（无分组标题）
./run_paddle_ocr.sh images/cmb output_cmb.md ch

# 单独识别京东金融截图（无分组标题）
./run_paddle_ocr.sh images/jd output_jd.md ch

# 跳过 DeepSeek 清洗，查看原始 OCR 输出
./run_paddle_ocr.sh --skip-clean images output_raw.md ch

# 单独对已有 md 文件补跑 DeepSeek 清洗
./run_clean_ocr.sh output_all.md output_cleaned.md
```

### pdf-ocr — 扫描书籍转 Markdown

```bash
cd pdf-ocr

# 全量转换（PaddleOCR + DeepSeek 清洗）
./run_pdf_to_md.sh 书名.pdf 书名.md

# 先跳过清洗快速验证识别质量
./run_pdf_to_md.sh 书名.pdf test.md --skip-clean

# 只处理指定页范围（测试用）
./run_pdf_to_md.sh 书名.pdf test.md --pages 1-10 --skip-clean

# 调整渲染分辨率（默认 200 DPI，越高越慢越清晰）
./run_pdf_to_md.sh 书名.pdf 书名.md --dpi 250
```

---

## 环境配置

### Python 依赖（venv）

```bash
python3 -m venv venv
source venv/bin/activate
pip install paddlepaddle paddleocr pymupdf openai
```

### DeepSeek API Key（清洗步骤必须）

```bash
export DEEPSEEK_API_KEY="your-key-here"
```

使用 `--skip-clean` 可跳过此要求。

---

## 目录结构

```
OCR-Agent/
├── venv/                    # Python 虚拟环境（共用）
│
├── stock-ocr/               # 基金截图 OCR 流程
│   ├── images/              # 截图按券商分目录存放
│   │   ├── cmb/             # 招商银行截图
│   │   └── jd/              # 京东金融截图
│   ├── paddle_ocr_to_md.py  # 主程序（OCR + 清洗）
│   ├── clean_ocr.py         # DeepSeek 持仓噪声清洗模块
│   ├── ocr_worker.py        # JSON bridge worker
│   ├── run_paddle_ocr.sh    # ⭐ 便捷运行脚本
│   ├── run_clean_ocr.sh     # 单独补跑清洗
│   └── validation.md        # 清洗校验参考
│
├── pdf-ocr/                 # PDF 书籍 OCR 流程
│   ├── pdf_to_md.py         # 主程序（PDF→图片→OCR→清洗）
│   ├── clean_book_ocr.py    # DeepSeek 书籍噪声清洗模块
│   └── run_pdf_to_md.sh     # ⭐ 便捷运行脚本
│
└── README.md
```

---

## 输出格式

两个流程输出的 Markdown 格式相同，页/图片之间用 `>>>` 分隔：

```
<第1页文字>

>>>

<第2页文字>
```

---

## 识别质量

- ✅ 中文识别：95%+ 准确率（PaddleOCR PP-OCRv5）
- ✅ 数字金额：99%+ 准确率
- ✅ 完全本地运行（OCR 部分）
- ✅ DeepSeek 清洗去除页码、页眉、扫描噪点
