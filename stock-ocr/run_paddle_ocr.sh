#!/bin/bash
# PaddleOCR 便捷运行脚本
# 用法: ./run_paddle_ocr.sh <输入目录或文件> <输出.md> [语言]
#
# 图片目录结构:
#   images/cmb/   招商银行截图
#   images/jd/    京东金融截图
#
# 示例:
#   ./run_paddle_ocr.sh images/cmb output_cmb.md ch   # 招商银行
#   ./run_paddle_ocr.sh images/jd  output_jd.md  ch   # 京东金融
#   ./run_paddle_ocr.sh images     output_all.md ch   # 全部

source "$(dirname "$0")/../venv/bin/activate"
cd "$(dirname "$0")"
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True python paddle_ocr_to_md.py "$@"
