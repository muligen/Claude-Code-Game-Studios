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

## Prerequisites

**Python 3.8+** (bundled with macOS/Linux; install from python.org on Windows).

Install dependencies:
```bash
pip install -r .claude/skills/generate-art/requirements.txt
```

Only one external package:
- **Pillow** — for image dimension/format validation (Phase 3). The generation
  script itself uses only Python stdlib (`urllib`, `json`, `base64`).

**If Pillow is not installed**, generation still works — only the Phase 3
validation step (checking dimensions) will be skipped.

---

## Generation Script

A single cross-platform Python script handles all providers:

`.claude/skills/generate-art/scripts/generate_art.py`

| Provider | CLI name | Env Var | Key Options |
|----------|----------|---------|-------------|
| Alibaba Cloud Bailian wan2.6 | `bailian` | `DASHSCOPE_API_KEY` | `--size` (1280*1280 etc), `--region` (beijing/singapore/virginia) |
| OpenAI DALL-E 3 | `openai` | `OPENAI_API_KEY` | `--size` (1024x1024, 1792x1024, 1024x1792) |
| Stability AI | `stability` | `STABILITY_API_KEY` | `--aspect` (1:1, 16:9, 9:16, 4:3, 3:4, 3:2) |
| Local SD WebUI | `local-sd` | (none) | `--width`, `--height` |
| ComfyUI | `comfyui` | (none) | `--width`, `--height`, `--workflow` |

**To generate**: Execute via Bash:
```bash
python .claude/skills/generate-art/scripts/generate_art.py <provider> "<prompt>" "<output-path>" [options]
```

Example (Bailian):
```bash
python .claude/skills/generate-art/scripts/generate_art.py bailian "pixel art character, warrior, 32x32" "assets/art/sprites/char_warrior_01.png" --size "1280*1280"
```

Example (DALL-E):
```bash
python .claude/skills/generate-art/scripts/generate_art.py openai "pixel art character, warrior, 32x32" "assets/art/sprites/char_warrior_01.png" --size "1024x1024"
```

Example (ComfyUI with custom workflow):
```bash
python .claude/skills/generate-art/scripts/generate_art.py comfyui "pixel art warrior" "assets/art/sprites/warrior.png" --width 512 --height 512 --workflow "design/art/comfyui-pixel-workflow.json"
```

---

## API Key Configuration (.env)

API keys are stored in `.claude/skills/generate-art/.env` (gitignored).

**Setup**: Copy the example and fill in keys:
```bash
cp .claude/skills/generate-art/.env.example .claude/skills/generate-art/.env
# Edit .env and fill in your API key
```

The script auto-loads `.env` on startup. Keys can also be set as environment
variables (env vars take precedence over .env).

---

## Non-Secret Configuration

`design/art/api-config.md` — records provider choice and region/endpoint.
API keys are **never** in files tracked by git.

---

## Phase 1: Check Configuration

Before any generation:

1. Check dependencies: `python -c "import PIL; print('OK')"` — if missing, run:
   `pip install -r .claude/skills/generate-art/requirements.txt`
2. Read `design/art/api-config.md` for provider selection
3. Check `.env` or env var for the corresponding API key

### Config missing → Guided Setup

Use `AskUserQuestion`:

```
=== Image Generation API Configuration ===

Choose an image generation API:

1. Alibaba Cloud Bailian wan2.6 (recommended for China) — needs DASHSCOPE_API_KEY
2. OpenAI DALL-E 3 — needs OPENAI_API_KEY
3. Stability AI — needs STABILITY_API_KEY
4. Local Stable Diffusion WebUI — no API key needed
5. ComfyUI — no API key needed
6. Set up later
```

After selection:
- Guide user to copy `.env.example` to `.env` and fill in the key
- For Bailian: also ask region (beijing/singapore/virginia)
- For Local SD: ask endpoint URL (default http://localhost:7860)
- For ComfyUI: ask endpoint URL (default http://localhost:8188)

Create `design/art/api-config.md`:

```markdown
# Image Generation API Configuration

## Active Provider
- Provider: [bailian | openai | stability | local-sd | comfyui]
- Configured: [ISO date]

## Provider Settings
[Provider-specific non-secret settings: region, endpoint URL]

## Usage Notes
- API keys in .env file or env vars, never committed to git
- /generate-art status → verify config
- /generate-art setup → change provider
```

### Verify API key

```bash
python -c "from pathlib import Path; p=Path('.claude/skills/generate-art/.env'); print('FOUND' if p.exists() else 'MISSING')"
```

If key not configured:
> API key not found. Please edit `.claude/skills/generate-art/.env` and fill in your key.
> Or set the environment variable directly.

Do NOT proceed until the key is confirmed.

---

## Phase 2: Generate Image

Read the provider from `design/art/api-config.md`, then execute:

```bash
python .claude/skills/generate-art/scripts/generate_art.py <provider> "<prompt>" "<output-path>" [options]
```

The script handles all HTTP details, polling, download, and validation internally.
Wait for completion — async providers (Bailian, ComfyUI) may take 1-10 minutes.

---

## Phase 3: Validate Output

After script completes:

1. **File exists** and non-zero size
2. **Dimensions** — `python -c "from PIL import Image; print(Image.open('PATH').size)"`
3. **Format** — PNG for game assets (transparency)

If validation fails, report and offer retry.

---

## Status Mode

Read config and check .env:

```
=== Image Generation API Status ===
Provider: [name]
Env Var: [VAR_NAME] — [SET / NOT SET]
Config file: [EXISTS / MISSING]
.env file: [EXISTS / MISSING]

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
| API key not set | Show .env setup instructions, do not retry |
| 401/403 | Key invalid, ask user to update .env |
| 429 | Rate limited, wait 30s, retry once |
| Task FAILED | Read error, adjust prompt, retry once |
| Download fails | Retry download up to 3 times |
| Network error | Check endpoint URL, suggest troubleshooting |
