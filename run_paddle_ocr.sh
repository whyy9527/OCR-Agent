#!/bin/bash
# PaddleOCR 便捷运行脚本

# 激活虚拟环境
source venv/bin/activate

# 运行 PaddleOCR
# 用法: ./run_paddle_ocr.sh <输入目录或文件> <输出.md> [语言]
# 示例: ./run_paddle_ocr.sh test_png output.md ch
python paddle_ocr_to_md.py "$@"
