#!/bin/bash
# 一次性 OCR 任务，跑完后自动从 crontab 删除自己
SCRIPT_DIR="$(dirname "$0")"
LOG="$SCRIPT_DIR/cron.log"

echo "[$(date)] 开始运行 OCR..." >> "$LOG"

DEEPSEEK_API_KEY='sk-cfde2a8a155243a1aa5a070e1363925f' \
  bash "$SCRIPT_DIR/run_pdf_to_md.sh" 起卦秘籍.pdf 起卦秘籍.md >> "$LOG" 2>&1

echo "[$(date)] OCR 完成，删除 cron job..." >> "$LOG"
crontab -l | grep -v "run_once_ocr.sh" | crontab -
