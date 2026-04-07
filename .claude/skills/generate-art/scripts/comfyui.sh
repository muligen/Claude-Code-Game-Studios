#!/bin/bash
# comfyui.sh — ComfyUI 本地生图
# 需要本地运行 ComfyUI，无需 API Key
# 用法: bash comfyui.sh "提示词" "输出路径" [宽] [高] [负面提示词] [工作流json路径]
#
# 工作流模式：如果提供第6个参数（工作流JSON路径），使用该工作流
# 默认模式：使用内置基础 txt2img 工作流

set -euo pipefail

PROMPT="${1:?用法: comfyui.sh <prompt> <output_path> [width] [height] [negative_prompt] [workflow_json]}"
OUTPUT="${2:?请指定输出路径}"
WIDTH="${3:-1024}"
HEIGHT="${4:-1024}"
NEGATIVE="${5:-low quality, blurry, deformed, watermark, text}"
WORKFLOW="${6:-}"
ENDPOINT="${COMFYUI_ENDPOINT:-http://localhost:8188}"

echo "[ComfyUI] 生成图片..."
echo "  端点: $ENDPOINT"
echo "  尺寸: ${WIDTH}x${HEIGHT}"

mkdir -p "$(dirname "$OUTPUT")"

# 构建工作流 JSON
if [ -n "$WORKFLOW" ] && [ -f "$WORKFLOW" ]; then
  # 使用用户提供的工作流文件，替换关键参数
  WORKFLOW_JSON=$(cat "$WORKFLOW" | \
    sed "s/__PROMPT__/${PROMPT}/g" | \
    sed "s/__NEGATIVE__/${NEGATIVE}/g" | \
    sed "s/__WIDTH__/${WIDTH}/g" | \
    sed "s/__HEIGHT__/${HEIGHT}/g")
  echo "  工作流: $WORKFLOW"
else
  # 内置基础 txt2img 工作流（适用于 SD1.5/SDXL 基础安装）
  WORKFLOW_JSON=$(cat <<'WORKFLOW_EOF'
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": "__SEED__",
      "steps": 30,
      "cfg": 7,
      "sampler_name": "dpmpp_2m",
      "scheduler": "karras",
      "denoise": 1,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    }
  },
  "4": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "__CHECKPOINT__"
    }
  },
  "5": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": __WIDTH__,
      "height": __HEIGHT__,
      "batch_size": 1
    }
  },
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "__PROMPT__",
      "clip": ["4", 1]
    }
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "__NEGATIVE__",
      "clip": ["4", 1]
    }
  },
  "8": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    }
  },
  "9": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "ccgs_gen",
      "images": ["8", 0]
    }
  }
}
WORKFLOW_EOF
  )
  # 替换参数
  SEED=$((RANDOM * 32768 + RANDOM))
  WORKFLOW_JSON=$(echo "$WORKFLOW_JSON" | \
    sed "s/__PROMPT__/${PROMPT}/g" | \
    sed "s/__NEGATIVE__/${NEGATIVE}/g" | \
    sed "s/__WIDTH__/${WIDTH}/g" | \
    sed "s/__HEIGHT__/${HEIGHT}/g" | \
    sed "s/__SEED__/${SEED}/g" | \
    sed "s/__CHECKPOINT__/$(ls models/checkpoints/*.safetensors 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo 'model.safetensors')/g")
fi

# Step 1: 提交工作流
SUBMIT_RESPONSE=$(curl -s -X POST "${ENDPOINT}/prompt" \
  -H 'Content-Type: application/json' \
  -d "{\"prompt\": ${WORKFLOW_JSON}}")

# 检查是否提交成功
PROMPT_ID=$(echo "$SUBMIT_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['prompt_id'])" 2>/dev/null)

if [ -z "$PROMPT_ID" ]; then
  echo "[ComfyUI] 提交失败:"
  echo "$SUBMIT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SUBMIT_RESPONSE"
  echo ""
  echo "排查建议:"
  echo "  1. ComfyUI 是否在运行？访问 ${ENDPOINT} 确认"
  echo "  2. 如果用默认工作流，确保 models/checkpoints/ 下有模型文件"
  echo "  3. 如果用自定义工作流，检查 JSON 格式和节点 ID"
  exit 1
fi

echo "[ComfyUI] 已提交，Prompt ID: $PROMPT_ID"
echo "[ComfyUI] 等待生成..."

# Step 2: 轮询执行状态
MAX_POLLS=120  # 最多等20分钟
POLL_COUNT=0
STATUS="pending"

while [ "$STATUS" = "pending" ] || [ "$STATUS" = "running" ]; do
  POLL_COUNT=$((POLL_COUNT + 1))
  if [ $POLL_COUNT -gt $MAX_POLLS ]; then
    echo "[ComfyUI] 超时 (等待超过20分钟)"
    exit 1
  fi
  sleep 10

  HISTORY=$(curl -s "${ENDPOINT}/history/${PROMPT_ID}")

  # 检查是否有输出
  STATUS=$(echo "$HISTORY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if PROMPT_ID not in data:
    print('running')
else:
    status_data = data[PROMPT_ID]
    if 'status' in status_data and status_data['status'].get('completed', False):
        print('done')
    elif 'status' in status_data and status_data['status'].get('status_str') == 'error':
        print('error')
    else:
        print('running')
" 2>/dev/null || echo "running")

  echo "[ComfyUI] 状态: $STATUS (${POLL_COUNT}/$MAX_POLLS)"
done

if [ "$STATUS" = "error" ]; then
  echo "[ComfyUI] 执行出错:"
  echo "$HISTORY" | python3 -m json.tool 2>/dev/null || echo "$HISTORY"
  exit 1
fi

# Step 3: 提取并下载生成的图片
IMAGE_INFO=$(echo "$HISTORY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
prompt_data = data.get(PROMPT_ID, {})
outputs = prompt_data.get('outputs', {})
# 查找 SaveImage 节点（通常是节点 9，但也可能是其他）
for node_id, node_output in outputs.items():
    if 'images' in node_output:
        for img in node_output['images']:
            print(f\"{img.get('filename','')}|{img.get('subfolder','')}\")
            sys.exit(0)
print('', file=sys.stderr)
" 2>/dev/null)

if [ -z "$IMAGE_INFO" ]; then
  echo "[ComfyUI] 未找到输出图片"
  exit 1
fi

FILENAME=$(echo "$IMAGE_INFO" | cut -d'|' -f1)
SUBFOLDER=$(echo "$IMAGE_INFO" | cut -d'|' -f2)

# 通过 ComfyUI 的 /view 端点下载
DOWNLOAD_URL="${ENDPOINT}/view?filename=${FILENAME}&subfolder=${SUBFOLDER}&type=output"
echo "[ComfyUI] 下载图片..."
curl -s -o "$OUTPUT" "$DOWNLOAD_URL"

# 验证
if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
  FILE_SIZE=$(stat -f%z "$OUTPUT" 2>/dev/null || stat -c%s "$OUTPUT" 2>/dev/null || echo "unknown")
  echo "[ComfyUI] 完成: $OUTPUT ($FILE_SIZE bytes)"
else
  echo "[ComfyUI] 下载失败"
  echo "  手动下载: $DOWNLOAD_URL"
  exit 1
fi
