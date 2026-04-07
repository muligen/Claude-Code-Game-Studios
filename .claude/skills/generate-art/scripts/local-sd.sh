#!/bin/bash
# local-sd.sh — 本地 Stable Diffusion WebUI 生图
# 无需 API Key，需本地运行 SD WebUI
# 用法: bash local-sd.sh "提示词" "输出路径" [宽] [高] [负面提示词]

set -euo pipefail

PROMPT="${1:?用法: local-sd.sh <prompt> <output_path> [width] [height] [negative_prompt]}"
OUTPUT="${2:?请指定输出路径}"
WIDTH="${3:-1024}"
HEIGHT="${4:-1024}"
NEGATIVE="${5:-low quality, blurry, deformed, watermark}"
ENDPOINT="${SD_ENDPOINT:-http://localhost:7860}"

echo "[Local-SD] 生成图片..."
echo "  端点: $ENDPOINT"
echo "  尺寸: ${WIDTH}x${HEIGHT}"

RESPONSE=$(curl -s -X POST "${ENDPOINT}/sdapi/v1/txt2img" \
  -H 'Content-Type: application/json' \
  -d "$(cat <<EOF
{
  "prompt": "${PROMPT}",
  "negative_prompt": "${NEGATIVE}",
  "width": ${WIDTH},
  "height": ${HEIGHT},
  "steps": 30,
  "cfg_scale": 7,
  "sampler_name": "DPM++ 2M Karras"
}
EOF
)")

# 检查是否有错误
if echo "$RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); sys.exit(0 if 'images' in data else 1)" 2>/dev/null; then
  mkdir -p "$(dirname "$OUTPUT")"
  echo "$RESPONSE" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
with open('$OUTPUT', 'wb') as f:
    f.write(base64.b64decode(data['images'][0]))
"
  if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
    FILE_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")
    echo "[Local-SD] 完成: $OUTPUT ($FILE_SIZE bytes)"
  else
    echo "[Local-SD] 解码失败"
    exit 1
  fi
else
  echo "[Local-SD] 生成失败:"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
  exit 1
fi
