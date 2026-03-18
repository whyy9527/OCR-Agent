#!/bin/bash
# PDF 扫描书籍转 Markdown
# 用法: ./run_pdf_to_md.sh <input.pdf> <output.md> [选项]
# 示例: ./run_pdf_to_md.sh 起卦秘籍.pdf 起卦秘籍.md
#       ./run_pdf_to_md.sh 起卦秘籍.pdf test.md --pages 1-10 --skip-clean

source "$(dirname "$0")/../venv/bin/activate"
cd "$(dirname "$0")"
python3 pdf_to_md.py "$@"
