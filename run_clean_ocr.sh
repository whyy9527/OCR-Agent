#!/bin/bash
# OCR 噪声清理脚本
# 用法: ./run_clean_ocr.sh <输入.md> [输出.md]
# 输出.md 省略时覆盖输入文件
# 需要设置环境变量: export DEEPSEEK_API_KEY="your-key"

source venv/bin/activate
python3 clean_ocr.py "$@"
