#!/usr/bin/env python3
"""
OCR Worker — stdin/stdout JSON bridge for metis-essay-marker.

Protocol:
  Node.js writes one JSON line to stdin:
    {"base64": "<base64-encoded image>", "mime_type": "image/png", "lang": "ch"}

  This script writes one JSON line to stdout:
    {"text": "<extracted text>"}
  or on error:
    {"error": "<message>"}

  After the response, the process exits.
  Node.js spawns a fresh process per OCR request.
"""

import base64
import json
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def run() -> None:
    try:
        raw = sys.stdin.readline()
        if not raw:
            print(json.dumps({"error": "empty input"}), flush=True)
            return

        req = json.loads(raw)
        b64 = req.get("base64", "")
        lang = req.get("lang", "en")

        if not b64:
            print(json.dumps({"error": "missing base64 field"}), flush=True)
            return

        image_bytes = base64.b64decode(b64)

        # Write to a temp file — PaddleOCR works best with file paths
        suffix = ".png"
        mime = req.get("mime_type", "image/png")
        if "jpeg" in mime or "jpg" in mime:
            suffix = ".jpg"
        elif "webp" in mime:
            suffix = ".webp"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        try:
            from paddleocr import PaddleOCR  # noqa: PLC0415 — lazy import after arg parsing

            ocr = PaddleOCR(lang=lang)
            results = ocr.predict(input=tmp_path)

            text = ""
            if results:
                result = results[0]
                if hasattr(result, "rec_texts") and result.rec_texts:
                    text = "\n".join(result.rec_texts).strip()
                elif isinstance(result, dict) and "rec_texts" in result:
                    text = "\n".join(result["rec_texts"]).strip()

            print(json.dumps({"text": text}), flush=True)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid JSON: {exc}"}), flush=True)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}), flush=True)


if __name__ == "__main__":
    run()
