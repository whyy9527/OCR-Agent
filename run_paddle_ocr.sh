#!/bin/bash
# PaddleOCR 便捷运行脚本
# 运行 PaddleOCR
# 用法: ./run_paddle_ocr.sh <输入目录或文件> <输出.md> [语言]
# 示例: ./run_paddle_ocr.sh test_png output.md ch

source venv/bin/activate
python paddle_ocr_to_md.py "$@"
