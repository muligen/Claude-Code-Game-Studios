---
name: generate-art
description: "Generate game art assets using configured image generation API (Bailian wan2.6, DALL-E, Stability, local SD, ComfyUI). Handles config check, guided setup, API calls, and download. First run guides user through API provider selection."
argument-hint: "[prompt text] or 'setup' to reconfigure API, 'status' to check config"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion
---

# Generate Art — Image Generation Skill

Handles image generation API calls: config check, guided setup, API dispatch,
download, and validation.

---

## Arguments

- **`[prompt text]`** — Generate an image with the given prompt
- **`setup`** — Reconfigure API provider (interactive)
- **`status`** — Show current API configuration

---

## Provider Scripts

Each provider has a standalone script in `.claude/skills/generate-art/scripts/`:

| Provider | Script | Env Var | Sizes |
|----------|--------|---------|-------|
| 阿里云百炼万相2.6 | `bailian-wanx.sh` | `DASHSCOPE_API_KEY` | `1280*1280`, `1280*720`, `720*1280`, `1280*960`, `960*1280`, `1200*800`, `800*1200`, `1344*576` |
| OpenAI DALL-E 3 | `openai-dalle.sh` | `OPENAI_API_KEY` | `1024x1024`, `1792x1024`, `1024x1792` |
| Stability AI | `stability.sh` | `STABILITY_API_KEY` | aspect ratios: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2` |
| Local SD WebUI | `local-sd.sh` | (none) | custom WxH |
| ComfyUI | `comfyui.sh` | (none) | custom WxH，支持自定义工作流 JSON |

**To call a provider**: Read the script file first (to get exact usage), then
execute via Bash. Scripts handle all HTTP details, polling, and download.

---

## Configuration File

`design/art/api-config.md` — records provider choice and non-secret settings.
API keys are **never** in files; always in environment variables.

---

## Phase 1: Check Configuration

Before any generation, read `design/art/api-config.md`.

### Config missing → Guided Setup

Use `AskUserQuestion`:

```
=== 图像生成 API 配置 ===

需要配置一个图像生成 API 才能生成美术素材。请选择：

1. 阿里云百炼万相2.6（推荐中国用户）— 需要 DASHSCOPE_API_KEY
2. OpenAI DALL-E 3 — 需要 OPENAI_API_KEY
3. Stability AI — 需要 STABILITY_API_KEY
4. 本地 Stable Diffusion WebUI — 无需 API Key
5. ComfyUI — 无需 API Key
6. 稍后配置
```

After selection, ask for required info:
- **Bailian**: set `DASHSCOPE_API_KEY`, choose region (北京/新加坡/弗吉尼亚)
- **OpenAI**: set `OPENAI_API_KEY`
- **Stability**: set `STABILITY_API_KEY`
- **Local SD**: endpoint URL (default `http://localhost:7860`)
- **ComfyUI**: endpoint URL (default `http://localhost:8188`)

Create `design/art/api-config.md`:

```markdown
# Image Generation API Configuration

## Active Provider
- Provider: [bailian | openai | stability | local-sd | comfyui]
- Configured: [ISO date]

## Provider Settings
[Provider-specific non-secret settings: region, endpoint URL]

## Usage Notes
- API keys in env vars only, never committed to git
- /generate-art status → verify config
- /generate-art setup → change provider
```

### Verify env var

```bash
echo $DASHSCOPE_API_KEY  # or OPENAI_API_KEY, STABILITY_API_KEY
```

If not set:
> 环境变量 `[VAR_NAME]` 未设置。请先设置：
> - 临时：`export DASHSCOPE_API_KEY=sk-xxx`
> - 永久：添加到 `~/.bashrc` 或 `~/.zshrc`

Do NOT proceed until the key is confirmed.

---

## Phase 2: Generate Image

Read the provider from `design/art/api-config.md`, then:

1. **Read the matching script** from `.claude/skills/generate-art/scripts/`
2. **Execute** via Bash with: `bash <script-path> "<prompt>" "<output-path>" [size] [negative-prompt]`
3. **Wait for completion** — scripts handle polling and download internally

Example (Bailian):
```bash
bash .claude/skills/generate-art/scripts/bailian-wanx.sh "pixel art character, warrior, 32x32" "assets/art/sprites/char_warrior_01_32x32.png" "1280*1280"
```

Example (DALL-E):
```bash
bash .claude/skills/generate-art/scripts/openai-dalle.sh "pixel art character, warrior, 32x32" "assets/art/sprites/char_warrior_01_32x32.png" "1024x1024"
```

Example (ComfyUI with custom workflow):
```bash
bash .claude/skills/generate-art/scripts/comfyui.sh "pixel art warrior" "assets/art/sprites/warrior.png" 512 512 "" "design/art/comfyui-pixel-workflow.json"
```

---

## Phase 3: Validate Output

After script completes:

1. **File exists** and non-zero size
2. **Dimensions** — `python3 -c "from PIL import Image; print(Image.open('PATH').size)"`
3. **Format** — PNG for game assets (transparency)

If validation fails, report and offer retry.

---

## Status Mode

Read config and check env var:

```
=== Image Generation API Status ===
Provider: [name]
Env Var: [VAR_NAME] — [SET / NOT SET]
Endpoint: [URL]
Config file: [EXISTS / MISSING]

Ready: [YES / NO — reason]
```

---

## Setup Mode

Delete `design/art/api-config.md` and restart Phase 1.

---

## Prompt Construction Rules

Every prompt must include:

1. **Style anchor**: From art bible (e.g., "pixel art style, 16-color palette, warm earth tones")
2. **Subject**: What the asset depicts
3. **Technical constraints**: Dimensions, transparency, format
4. **Negative prompt** (where supported): "no text, no watermark, no blur, low quality, deformed"
5. **Consistency anchor**: For batch assets, reference first asset's style parameters

---

## Error Handling

| Error | Action |
|-------|--------|
| API key not set | Show setup instructions, do not retry |
| 401/403 | Key invalid, ask user to update env var |
| 429 | Rate limited, wait 30s, retry once |
| Task FAILED | Read error, adjust prompt, retry once |
| Download fails | Retry download up to 3 times |
| Image URL expired (24h) | Re-run generation |
