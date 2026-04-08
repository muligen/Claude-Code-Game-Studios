#!/usr/bin/env python3
"""
generate_art.py — Cross-platform image generation script for CCGS.

Supports 5 providers:
  bailian   — Alibaba Cloud Bailian wan2.6 (async)
  openai    — OpenAI DALL-E 3
  stability — Stability AI
  local-sd  — Local Stable Diffusion WebUI
  comfyui   — ComfyUI (built-in or custom workflow)

API keys are loaded from:
  1. Environment variables
  2. .env file in the skill directory (.claude/skills/generate-art/.env)

Usage:
  python generate_art.py bailian   "prompt" "output.png" [size] [negative] [region]
  python generate_art.py openai    "prompt" "output.png" [size]
  python generate_art.py stability "prompt" "output.png" [aspect_ratio]
  python generate_art.py local-sd  "prompt" "output.png" [width] [height] [negative]
  python generate_art.py comfyui   "prompt" "output.png" [width] [height] [negative] [workflow.json]
"""

import argparse
import base64
import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def load_env():
    """Load .env file from the skill directory (does not override existing env vars)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_env(key: str) -> str:
    """Get an environment variable, raise if missing."""
    value = os.environ.get(key, "")
    if not value:
        print(f"[ERROR] 环境变量 {key} 未设置。", file=sys.stderr)
        print(f"  请编辑 .claude/skills/generate-art/.env 文件，填入 {key}", file=sys.stderr)
        sys.exit(1)
    return value


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_post(url: str, headers: dict, body: dict | str | None = None,
              form_data: dict | None = None, accept_binary: bool = False):
    """Send a POST request. Returns (status_code, response_bytes_or_json)."""
    if isinstance(body, dict):
        data = json.dumps(body).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
    elif isinstance(body, str):
        data = body.encode("utf-8")
    elif form_data is not None:
        # multipart/form-data
        boundary = f"----CCGS{random.randint(0, 999999)}"
        parts = []
        for k, v in form_data.items():
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}")
        parts.append(f"--{boundary}--\r\n")
        data = ("\r\n".join(parts)).encode("utf-8")
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        data = None

    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            resp_data = resp.read()
            if accept_binary:
                return resp.status, resp_data
            return resp.status, json.loads(resp_data.decode("utf-8"))
    except HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        try:
            body_json = json.loads(body_text)
        except json.JSONDecodeError:
            body_json = {"raw": body_text}
        return e.code, body_json
    except URLError as e:
        return 0, {"error": f"Network error: {e.reason}"}


def http_get(url: str, headers: dict | None = None):
    """Send a GET request. Returns (status_code, response_json)."""
    req = Request(url, headers=headers or {}, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body_text)
        except json.JSONDecodeError:
            return e.code, {"raw": body_text}
    except URLError as e:
        return 0, {"error": f"Network error: {e.reason}"}


def download_file(url: str, output_path: str):
    """Download a file from URL to local path."""
    req = Request(url)
    with urlopen(req, timeout=120) as resp:
        with open(output_path, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def ensure_parent(path: str):
    """Create parent directories if needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def validate_output(path: str) -> int:
    """Validate output file exists and return size. Exit on failure."""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        print(f"[ERROR] 生成失败: 文件不存在或为空 — {path}", file=sys.stderr)
        sys.exit(1)
    size = p.stat().st_size
    print(f"[OK] 完成: {path} ({size} bytes)")
    return size


# ---------------------------------------------------------------------------
# Provider: Bailian wan2.6 (async)
# ---------------------------------------------------------------------------

BAILIAN_HOSTS = {
    "beijing": "dashscope.aliyuncs.com",
    "singapore": "dashscope-intl.aliyuncs.com",
    "virginia": "dashscope-us.aliyuncs.com",
}

BAILIAN_SIZES = [
    "1280*1280", "1280*720", "720*1280", "1280*960",
    "960*1280", "1200*800", "800*1200", "1344*576",
]


def provider_bailian(prompt: str, output: str, size: str = "1280*1280",
                     negative: str = "low quality, blurry, deformed, watermark, text",
                     region: str = "beijing"):
    api_key = get_env("DASHSCOPE_API_KEY")
    host = BAILIAN_HOSTS.get(region, BAILIAN_HOSTS["beijing"])
    base = f"https://{host}/api/v1"

    print(f"[Bailian] 创建异步任务...")
    print(f"  端点: {host}")
    print(f"  尺寸: {size}")

    # Step 1: Submit async task
    status, resp = http_post(
        f"{base}/services/aigc/image-generation/generation",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        },
        body={
            "model": "wan2.6-image",
            "input": {
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            },
            "parameters": {
                "size": size,
                "n": 1,
                "watermark": False,
                "negative_prompt": negative,
                "enable_interleave": True,
            }
        }
    )

    # Extract task_id
    task_id = ""
    if isinstance(resp, dict):
        task_id = resp.get("output", {}).get("task_id", "")
        if not task_id and "error" in resp:
            print(f"[Bailian] 任务创建失败: {resp}", file=sys.stderr)
            sys.exit(1)

    if not task_id:
        print(f"[Bailian] 任务创建失败，无法获取 task_id", file=sys.stderr)
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print(f"[Bailian] 任务ID: {task_id}")
    print(f"[Bailian] 轮询结果 (每10秒)...")

    # Step 2: Poll for completion
    max_polls = 60  # 10 minutes max
    for i in range(1, max_polls + 1):
        time.sleep(10)
        _, result = http_get(
            f"{base}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        task_status = result.get("output", {}).get("task_status", "UNKNOWN")
        print(f"[Bailian] 状态: {task_status} ({i}/{max_polls})")

        if task_status == "SUCCEEDED":
            # Step 3: Extract image URL
            image_url = ""
            for choice in result.get("output", {}).get("choices", []):
                for item in choice.get("message", {}).get("content", []):
                    if item.get("type") == "image":
                        image_url = item.get("image", "")
                        break
                if image_url:
                    break

            if not image_url:
                print("[Bailian] 未找到图片URL", file=sys.stderr)
                print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
                sys.exit(1)

            # Step 4: Download
            print("[Bailian] 下载图片...")
            ensure_parent(output)
            download_file(image_url, output)
            validate_output(output)
            return

        elif task_status in ("FAILED", "ERROR", "CANCELED"):
            print(f"[Bailian] 任务失败: {task_status}", file=sys.stderr)
            print(json.dumps(result, indent=2, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    print("[Bailian] 超时 (等待超过10分钟)", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Provider: OpenAI DALL-E 3
# ---------------------------------------------------------------------------

DALLE_SIZES = ["1024x1024", "1792x1024", "1024x1792"]


def provider_openai(prompt: str, output: str, size: str = "1024x1024"):
    api_key = get_env("OPENAI_API_KEY")

    print(f"[DALL-E] 生成图片...")
    print(f"  尺寸: {size}")

    status, resp = http_post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "hd",
            "response_format": "url",
        }
    )

    if isinstance(resp, dict) and "error" in resp:
        print(f"[DALL-E] 生成失败: {resp['error']}", file=sys.stderr)
        sys.exit(1)

    image_url = ""
    try:
        image_url = resp["data"][0]["url"]
    except (KeyError, IndexError, TypeError):
        print(f"[DALL-E] 响应格式异常", file=sys.stderr)
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print("[DALL-E] 下载图片...")
    ensure_parent(output)
    download_file(image_url, output)
    validate_output(output)


# ---------------------------------------------------------------------------
# Provider: Stability AI
# ---------------------------------------------------------------------------

STABILITY_ASPECTS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2"]


def provider_stability(prompt: str, output: str, aspect: str = "1:1"):
    api_key = get_env("STABILITY_API_KEY")

    print(f"[Stability] 生成图片...")
    print(f"  比例: {aspect}")

    # Stability API needs multipart form
    boundary = f"----CCGS{random.randint(0, 999999)}"
    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n{prompt}")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"aspect_ratio\"\r\n\r\n{aspect}")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"output_format\"\r\n\r\npng")
    parts.append(f"--{boundary}--\r\n")
    data = ("\r\n".join(parts)).encode("utf-8")

    ensure_parent(output)
    req = Request(
        "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=120) as resp:
            if resp.status != 200:
                print(f"[Stability] 请求失败: HTTP {resp.status}", file=sys.stderr)
                sys.exit(1)
            with open(output, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
    except HTTPError as e:
        print(f"[Stability] 请求失败: HTTP {e.code}", file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        sys.exit(1)

    validate_output(output)


# ---------------------------------------------------------------------------
# Provider: Local SD WebUI
# ---------------------------------------------------------------------------

def provider_local_sd(prompt: str, output: str, width: int = 1024, height: int = 1024,
                      negative: str = "low quality, blurry, deformed, watermark"):
    endpoint = os.environ.get("SD_ENDPOINT", "http://localhost:7860")

    print(f"[Local-SD] 生成图片...")
    print(f"  端点: {endpoint}")
    print(f"  尺寸: {width}x{height}")

    status, resp = http_post(
        f"{endpoint}/sdapi/v1/txt2img",
        headers={"Content-Type": "application/json"},
        body={
            "prompt": prompt,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "steps": 30,
            "cfg_scale": 7,
            "sampler_name": "DPM++ 2M Karras",
        }
    )

    if isinstance(resp, dict) and "error" in resp and "images" not in resp:
        print(f"[Local-SD] 生成失败:", file=sys.stderr)
        print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    images = resp.get("images", [])
    if not images:
        print("[Local-SD] 响应中没有图片数据", file=sys.stderr)
        sys.exit(1)

    ensure_parent(output)
    with open(output, "wb") as f:
        f.write(base64.b64decode(images[0]))

    validate_output(output)


# ---------------------------------------------------------------------------
# Provider: ComfyUI
# ---------------------------------------------------------------------------

def provider_comfyui(prompt: str, output: str, width: int = 1024, height: int = 1024,
                     negative: str = "low quality, blurry, deformed, watermark, text",
                     workflow_path: str = ""):
    endpoint = os.environ.get("COMFYUI_ENDPOINT", "http://localhost:8188")

    print(f"[ComfyUI] 生成图片...")
    print(f"  端点: {endpoint}")
    print(f"  尺寸: {width}x{height}")

    # Build workflow JSON
    if workflow_path and Path(workflow_path).exists():
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_text = f.read()
        workflow_text = (workflow_text
                         .replace("__PROMPT__", prompt)
                         .replace("__NEGATIVE__", negative)
                         .replace("__WIDTH__", str(width))
                         .replace("__HEIGHT__", str(height)))
        workflow = json.loads(workflow_text)
        print(f"  工作流: {workflow_path}")
    else:
        # Built-in basic txt2img workflow (SD1.5/SDXL)
        # Try to find a checkpoint
        ckpt_dir = Path("models/checkpoints")
        ckpt_name = "model.safetensors"
        if ckpt_dir.exists():
            safetensors = list(ckpt_dir.glob("*.safetensors"))
            if safetensors:
                ckpt_name = safetensors[0].name

        seed = random.randint(0, 2**31)
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed, "steps": 30, "cfg": 7,
                    "sampler_name": "dpmpp_2m", "scheduler": "karras",
                    "denoise": 1, "model": ["4", 0],
                    "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["5", 0],
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": ckpt_name}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative, "clip": ["4", 1]}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "ccgs_gen", "images": ["8", 0]}
            },
        }

    # Step 1: Submit workflow
    status, resp = http_post(
        f"{endpoint}/prompt",
        headers={"Content-Type": "application/json"},
        body={"prompt": workflow}
    )

    prompt_id = ""
    if isinstance(resp, dict):
        prompt_id = resp.get("prompt_id", "")
        if not prompt_id:
            print("[ComfyUI] 提交失败:", file=sys.stderr)
            print(json.dumps(resp, indent=2, ensure_ascii=False), file=sys.stderr)
            print("", file=sys.stderr)
            print("排查建议:", file=sys.stderr)
            print("  1. ComfyUI 是否在运行？", file=sys.stderr)
            print("  2. models/checkpoints/ 下有模型文件吗？", file=sys.stderr)
            sys.exit(1)

    print(f"[ComfyUI] 已提交，Prompt ID: {prompt_id}")
    print("[ComfyUI] 等待生成...")

    # Step 2: Poll execution status
    max_polls = 120  # 20 minutes max
    for i in range(1, max_polls + 1):
        time.sleep(10)
        _, history = http_get(f"{endpoint}/history/{prompt_id}")

        if not isinstance(history, dict) or prompt_id not in history:
            print(f"[ComfyUI] 状态: running ({i}/{max_polls})")
            continue

        status_data = history[prompt_id].get("status", {})
        if status_data.get("completed", False):
            # Step 3: Extract image info
            outputs = history[prompt_id].get("outputs", {})
            filename = ""
            subfolder = ""
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        filename = img.get("filename", "")
                        subfolder = img.get("subfolder", "")
                        break
                if filename:
                    break

            if not filename:
                print("[ComfyUI] 未找到输出图片", file=sys.stderr)
                sys.exit(1)

            # Download via /view endpoint
            dl_url = f"{endpoint}/view?filename={filename}&subfolder={subfolder}&type=output"
            print("[ComfyUI] 下载图片...")
            ensure_parent(output)
            download_file(dl_url, output)
            validate_output(output)
            return

        elif status_data.get("status_str") == "error":
            print("[ComfyUI] 执行出错:", file=sys.stderr)
            print(json.dumps(history, indent=2, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

        print(f"[ComfyUI] 状态: running ({i}/{max_polls})")

    print("[ComfyUI] 超时 (等待超过20分钟)", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

PROVIDERS = {
    "bailian": {
        "func": provider_bailian,
        "help": "阿里云百炼万相2.6 (async)",
        "defaults": {"size": "1280*1280", "negative": "low quality, blurry, deformed, watermark, text", "region": "beijing"},
    },
    "openai": {
        "func": provider_openai,
        "help": "OpenAI DALL-E 3",
        "defaults": {"size": "1024x1024"},
    },
    "stability": {
        "func": provider_stability,
        "help": "Stability AI",
        "defaults": {"aspect_ratio": "1:1"},
    },
    "local-sd": {
        "func": provider_local_sd,
        "help": "本地 Stable Diffusion WebUI",
        "defaults": {"width": 1024, "height": 1024, "negative": "low quality, blurry, deformed, watermark"},
    },
    "comfyui": {
        "func": provider_comfyui,
        "help": "ComfyUI (built-in or custom workflow)",
        "defaults": {"width": 1024, "height": 1024, "negative": "low quality, blurry, deformed, watermark, text", "workflow": ""},
    },
}


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="CCGS Image Generation — 跨平台图像生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {name:12s} {info['help']}" for name, info in PROVIDERS.items()),
    )
    parser.add_argument("provider", choices=PROVIDERS.keys(), help="图像生成提供商")
    parser.add_argument("prompt", help="图像生成提示词")
    parser.add_argument("output", help="输出文件路径")
    parser.add_argument("--size", help="Bailian: 分辨率 (默认 1280*1280)")
    parser.add_argument("--negative", help="负面提示词")
    parser.add_argument("--region", help="Bailian: 区域 (beijing/singapore/virginia)")
    parser.add_argument("--aspect", help="Stability: 宽高比 (默认 1:1)")
    parser.add_argument("--width", type=int, help="Local-SD/ComfyUI: 宽度")
    parser.add_argument("--height", type=int, help="Local-SD/ComfyUI: 高度")
    parser.add_argument("--workflow", help="ComfyUI: 自定义工作流 JSON 路径")

    args = parser.parse_args()
    provider_info = PROVIDERS[args.provider]
    defaults = provider_info["defaults"]

    # Route to provider with merged defaults
    if args.provider == "bailian":
        provider_bailian(
            prompt=args.prompt,
            output=args.output,
            size=args.size or defaults["size"],
            negative=args.negative or defaults["negative"],
            region=args.region or defaults["region"],
        )
    elif args.provider == "openai":
        provider_openai(
            prompt=args.prompt,
            output=args.output,
            size=args.size or defaults["size"],
        )
    elif args.provider == "stability":
        provider_stability(
            prompt=args.prompt,
            output=args.output,
            aspect=args.aspect or defaults["aspect_ratio"],
        )
    elif args.provider == "local-sd":
        provider_local_sd(
            prompt=args.prompt,
            output=args.output,
            width=args.width or defaults["width"],
            height=args.height or defaults["height"],
            negative=args.negative or defaults["negative"],
        )
    elif args.provider == "comfyui":
        provider_comfyui(
            prompt=args.prompt,
            output=args.output,
            width=args.width or defaults["width"],
            height=args.height or defaults["height"],
            negative=args.negative or defaults["negative"],
            workflow_path=args.workflow or defaults["workflow"],
        )


if __name__ == "__main__":
    main()
