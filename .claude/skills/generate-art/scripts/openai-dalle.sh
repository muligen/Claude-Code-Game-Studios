#!/bin/bash
# openai-dalle.sh — OpenAI DALL-E 3 文生图
# 调用前需设置: OPENAI_API_KEY
# 用法: bash openai-dalle.sh "提示词" "输出路径" "尺寸"

set -euo pipefail

PROMPT="${1:?用法: openai-dalle.sh <prompt> <output_path> [size]}"
OUTPUT="${2:?请指定输出路径}"
SIZE="${3:-1024x1024}"

echo "[DALL-E] 生成图片..."
echo "  尺寸: $SIZE"

RESPONSE=$(curl -s -X POST 'https://api.openai.com/v1/images/generations' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -d "$(cat <<EOF
{
  "model": "dall-e-3",
  "prompt": "${PROMPT}",
  "n": 1,
  "size": "${SIZE}",
  "quality": "hd",
  "response_format": "url"
}
EOF
)")

# 提取图片URL
IMAGE_URL=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'error' in data:
    print(f'ERROR: {data[\"error\"][\"message\"]}', file=sys.stderr)
    sys.exit(1)
print(data['data'][0]['url'])
" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$IMAGE_URL" ]; then
  echo "[DALL-E] 生成失败:"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

echo "[DALL-E] 下载图片..."
mkdir -p "$(dirname "$OUTPUT")"
curl -s -o "$OUTPUT" "$IMAGE_URL"

if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
  FILE_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")
  echo "[DALL-E] 完成: $OUTPUT ($FILE_SIZE bytes)"
else
  echo "[DALL-E] 下载失败"
  exit 1
fi
