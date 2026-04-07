#!/bin/bash
# bailian-wanx.sh — 阿里云百炼万相2.6 异步生图
# 调用前需设置: DASHSCOPE_API_KEY
# 用法: bash bailian-wanx.sh "提示词" "输出路径" "分辨率" "负面提示词" "区域"

set -euo pipefail

PROMPT="${1:?用法: bailian-wanx.sh <prompt> <output_path> [size] [negative_prompt] [region]}"
OUTPUT="${2:?请指定输出路径}"
SIZE="${3:-1280*1280}"
NEGATIVE="${4:-low quality, blurry, deformed, watermark, text}"
REGION="${5:-beijing}"

# 区域端点映射
case "$REGION" in
  singapore) HOST="dashscope-intl.aliyuncs.com" ;;
  virginia) HOST="dashscope-us.aliyuncs.com" ;;
  *)        HOST="dashscope.aliyuncs.com" ;;
esac

echo "[Bailian] 创建异步任务..."
echo "  端点: $HOST"
echo "  尺寸: $SIZE"

# Step 1: 创建异步任务
TASK_RESPONSE=$(curl -s -X POST "https://${HOST}/api/v1/services/aigc/image-generation/generation" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${DASHSCOPE_API_KEY}" \
  -H 'X-DashScope-Async: enable' \
  -d "$(cat <<EOF
{
  "model": "wan2.6-image",
  "input": {
    "messages": [{"role": "user", "content": [{"text": "${PROMPT}"}]}]
  },
  "parameters": {
    "size": "${SIZE}",
    "n": 1,
    "watermark": false,
    "negative_prompt": "${NEGATIVE}",
    "enable_interleave": true
  }
}
EOF
)")

# 解析 task_id
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['output']['task_id'])" 2>/dev/null)

if [ -z "$TASK_ID" ]; then
  echo "[Bailian] 任务创建失败:"
  echo "$TASK_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TASK_RESPONSE"
  exit 1
fi

echo "[Bailian] 任务ID: $TASK_ID"
echo "[Bailian] 轮询结果 (每10秒)..."

# Step 2: 轮询任务状态
MAX_POLLS=60  # 最多等10分钟
POLL_COUNT=0
STATUS="PENDING"

while [ "$STATUS" = "PENDING" ] || [ "$STATUS" = "RUNNING" ]; do
  POLL_COUNT=$((POLL_COUNT + 1))
  if [ $POLL_COUNT -gt $MAX_POLLS ]; then
    echo "[Bailian] 超时 (等待超过10分钟)"
    exit 1
  fi
  sleep 10

  RESULT=$(curl -s -X GET "https://${HOST}/api/v1/tasks/${TASK_ID}" \
    -H "Authorization: Bearer ${DASHSCOPE_API_KEY}")

  STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['output']['task_status'])" 2>/dev/null || echo "UNKNOWN")
  echo "[Bailian] 状态: $STATUS (${POLL_COUNT}/$MAX_POLLS)"
done

# Step 3: 检查结果
if [ "$STATUS" != "SUCCEEDED" ]; then
  echo "[Bailian] 任务失败: $STATUS"
  echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
  exit 1
fi

# Step 4: 提取图片URL并下载
IMAGE_URL=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for choice in data['output']['choices']:
    for item in choice['message']['content']:
        if item.get('type') == 'image':
            print(item['image'])
            sys.exit(0)
" 2>/dev/null)

if [ -z "$IMAGE_URL" ]; then
  echo "[Bailian] 未找到图片URL"
  echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
  exit 1
fi

echo "[Bailian] 下载图片..."
mkdir -p "$(dirname "$OUTPUT")"
curl -s -o "$OUTPUT" "$IMAGE_URL"

# 验证文件
if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
  FILE_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")
  echo "[Bailian] 完成: $OUTPUT ($FILE_SIZE bytes)"
else
  echo "[Bailian] 下载失败或文件为空"
  exit 1
fi
