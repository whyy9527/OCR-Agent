#!/bin/bash
# PDF 扫描书籍转 Markdown
# 用法: ./run_pdf_to_md.sh <input.pdf> <output.md> [选项]
# 示例: ./run_pdf_to_md.sh 起卦秘籍.pdf 起卦秘籍.md
#       ./run_pdf_to_md.sh 起卦秘籍.pdf test.md --pages 1-10 --skip-clean

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/../venv/bin/python3"
cd "$SCRIPT_DIR"
"$VENV_PYTHON" pdf_to_md.py "$@"
