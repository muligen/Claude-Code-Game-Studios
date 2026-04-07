#!/bin/bash
# stability.sh — Stability AI 生图
# 调用前需设置: STABILITY_API_KEY
# 用法: bash stability.sh "提示词" "输出路径" "宽高比"

set -euo pipefail

PROMPT="${1:?用法: stability.sh <prompt> <output_path> [aspect_ratio]}"
OUTPUT="${2:?请指定输出路径}"
ASPECT="${3:-1:1}"

echo "[Stability] 生成图片..."
echo "  比例: $ASPECT"

mkdir -p "$(dirname "$OUTPUT")"
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$OUTPUT" -X POST \
  'https://api.stability.ai/v2beta/stable-image/generate/sd3' \
  -H "Authorization: Bearer ${STABILITY_API_KEY}" \
  -H "Accept: image/*" \
  -F "prompt=${PROMPT}" \
  -F "aspect_ratio=${ASPECT}" \
  -F "output_format=png")

if [ "$HTTP_CODE" -ne 200 ]; then
  echo "[Stability] 请求失败: HTTP $HTTP_CODE"
  rm -f "$OUTPUT"
  exit 1
fi

if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
  FILE_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")
  echo "[Stability] 完成: $OUTPUT ($FILE_SIZE bytes)"
else
  echo "[Stability] 下载失败"
  exit 1
fi
