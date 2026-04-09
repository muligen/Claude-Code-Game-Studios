---
name: webgl-playtest
description: "通用 WebGL 游戏自动化跑测：分析任意 WebGL 游戏的源码和启动方式，用 Playwright 模拟玩家操作，探索边界场景，输出带截图的测试报告"
argument-hint: "[quick | full] [--url http://localhost:3000]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Write, AskUserQuestion
---

# WebGL Playtest — 通用游戏自动化跑测

用 Playwright 打开任意 WebGL 游戏，自动分析游戏玩法，模拟玩家操作，
探索边界场景，发现 bug，输出带截图的测试报告。

**这个 skill 不针对特定游戏。** 它通过阅读源码理解当前项目游戏的
启动方式、状态机、交互元素、游戏规则，然后动态生成针对性的测试脚本。

**Output:** `production/qa/webgl-playtest-[date].md`
**Screenshots:** `tests/playwright/screenshots/[date]/`
**Test Script:** `tests/playwright/webgl-playtest-[date].spec.ts`

---

## Phase 1: Environment Check

### 1.1 Parse Arguments

- `quick` — smoke path only (launch → start game → play one round → end).
  ~30s. **Default**.
- `full` — smoke + boundary exploration (edge cases, stress, all game states).
  ~2-3 min.
- `--url http://...` — game URL (default: `http://localhost:3000`)

### 1.2 Check Playwright

```bash
npx playwright --version 2>&1
```

If fails: "Playwright not installed. Run `npm install -D @playwright/test && npx playwright install chromium` then re-run `/webgl-playtest`." → **STOP**

### 1.3 Check Dev Server

```bash
curl -s -o /dev/null -w "%{http_code}" [URL] 2>&1 || echo "UNREACHABLE"
```

If not `200`: "Dev server not running at [URL]. Start with `npm run dev`, then re-run." → **STOP**

### 1.4 Verify Helper Library

Check `tests/playwright/helpers/phaser-helpers.ts` exists. If not: "Helper library missing at expected path." → **STOP**

Report: "Environment OK. Playwright [version], dev server at [URL], mode: [quick|full]."

---

## Phase 2: Game Source Analysis

This phase reads the project's source code to understand what game this is,
how it starts, what the player can do, and what states the game goes through.
**No assumptions about game type.** Everything is derived from source.

### 2.1 Detect Game Engine

Read `package.json` dependencies. Check for:
- `phaser` → Phaser (2D, canvas/WebGL)
- `pixi.js` → PixiJS (2D renderer)
- `three` → Three.js (3D)
- `@babylonjs/core` → Babylon.js (3D)
- No known engine → generic WebGL canvas game

Also read `.claude/docs/technical-preferences.md` for engine info.

Store the detected engine — it affects how we analyze source code and which
APIs to look for.

### 2.2 Find Entry Points and Scenes

Glob the `src/` directory to understand project structure:

- `src/main.ts` or `src/index.ts` → game bootstrap, config
- `src/scenes/**` → game scenes/states (Phaser)
- `src/states/**` → game states (Phaser legacy)
- `src/game/**` → game logic
- `src/components/**` → ECS components
- `src/ui/**` or `src/screens/**` → UI layers

Read the entry point file. Extract:
- **Game resolution** (width, height) — needed for coordinate mapping
- **Scene/state list** — which scenes exist and in what order
- **Scale mode** — how coordinates map to screen

### 2.3 Analyze Game Scenes / States

For each scene/state file found in 2.2:

**Identify the game lifecycle:**
- Search for enum-like patterns: `enum.*Phase`, `enum.*State`, `StateType`
- Search for string constants that look like state names: `'idle'`, `'playing'`,
  `'menu'`, `'gameover'`, `'paused'`, etc.
- Map transitions: what triggers a state change (button click? timer? event?)

**Identify interactive elements:**
- Search for `setInteractive`, `onClick`, `on('pointer`, `addEventListener`
- For each interactive element, extract:
  - **Label/text** — what the element says (button text, card label)
  - **Position** — x, y coordinates or layout relative to parent
  - **Size** — width, height
  - **Type** — button, card, slider, draggable, click area
  - **Callback** — what happens when clicked/interacted

**Identify player actions:**
- What can the player DO in this game? (play card, move character, shoot, jump,
  place piece, select menu item, etc.)
- What inputs does the game accept? (click, drag, keyboard, touch)

**Identify AI/auto behavior:**
- Does the game have AI opponents?
- What are their timing delays?
- Does the game auto-advance any state?

**Identify timing/animation constants:**
- Tween durations, timeout values, animation speeds
- Any `setTimeout`, `setInterval`, tween config with `duration`

### 2.4 Analyze Game Objects

Glob `src/objects/**`, `src/entities/**`, `src/prefabs/**`, or similar.

For each game object:
- Dimensions and hit area
- Visual state changes (selected, highlighted, disabled)
- Animation parameters
- Parent-child relationships (containers, groups)

### 2.5 Analyze Game Logic

Glob `src/utils/**`, `src/logic/**`, `src/systems/**`, or similar.

Extract:
- Core rules and validation (what constitutes a valid move/action?)
- Win/lose conditions
- Scoring/progression mechanics
- Any configurable parameters (speeds, limits, thresholds)

### 2.6 Build Game Analysis Report

Synthesize all findings into a structured analysis. Present to user:

```
## Game Analysis: [Game Name / "Unnamed Game"]

**Engine**: [Phaser 3.90 / PixiJS / Three.js / ...]
**Resolution**: [WxH]
**Game Type**: [Card Game / Platformer / Puzzle / Strategy / ...]

### Game States
[list all detected states and transitions]

### Interactive Elements
| # | Type | Label | Position (x, y) | Size | Action |
|---|------|-------|-------------------|------|--------|
| 1 | Button | "Start" | (640, 360) | 200x60 | startGame() |
| ... |

### Player Actions
- [action 1]: [how to trigger]
- [action 2]: [how to trigger]

### Timing Constants
| Constant | Value | Source |
|----------|-------|--------|
| Deal animation | 2500ms | GameScene.ts:42 |
| AI turn delay | 1000ms | GameScene.ts:88 |
| ... |

### Win/Lose Conditions
- Win: [condition]
- Lose: [condition]

### Start Game Flow
1. [step 1 to start a new game]
2. [step 2]
3. [gameplay begins]
```

If the analysis is insufficient (can't determine how to start the game,
can't find interactive elements), use `AskUserQuestion` to ask the user:
"I couldn't determine [specific thing] from the source code. Can you tell me
how [to start the game / what the player does / etc.]?"

**Do not guess.** If source analysis is ambiguous, ask the user.

---

## Phase 3: Generate Playwright Test Script

Based on the Phase 2 analysis, generate a tailored Playwright test script.
Every coordinate, timing value, and interaction sequence comes from the
analysis — nothing is hardcoded in this skill.

### 3.1 Prepare Output Directory

```bash
mkdir -p tests/playwright/screenshots/[date]
```

### 3.2 Generate Test Script

Write to `tests/playwright/webgl-playtest-[date].spec.ts`.

The generated script must:

**Imports:**
```typescript
import { test, expect } from '@playwright/test';
import {
  waitForCanvasReady,
  clickCanvas,
  screenshotStep,
  waitAndSnapshot,
  getCanvasBounds,
  clickCenter,
  randomCanvasClicks,
  detectDOMButtons,
  detectWebGL,
  evaluateInPage,
} from './helpers/phaser-helpers';
```

**Test 1 — Launch & Canvas (always generated):**
- Navigate to URL
- Verify canvas element exists
- Verify WebGL context is available
- Verify canvas dimensions match expected resolution
- Screenshot: `01-loaded`

**Test 2 — Start Game (always generated):**
Based on the "Start Game Flow" from Phase 2 analysis:
- Execute the sequence of clicks/actions to start a new game
- Use analyzed coordinates and timing
- Screenshot after each step: `02-start-step-N`
- Verify the game entered its gameplay state (by waiting the analyzed
  state transition time and taking a screenshot)

**Test 3 — Smoke Playthrough (always generated):**
- Follow the detected game loop: player action → wait for response → repeat
- Each player action uses the coordinates and methods found in Phase 2
- If the game has AI opponents, wait the analyzed AI delay between turns
- Safety limit: MAX_TURNS = 100 to prevent infinite loops
- Screenshot every N turns (or every state change)
- Detect game end: if the analysis found win/lose conditions, generate
  code that waits for the end state; otherwise use a time limit

**Test 4-N — Boundary Tests (full mode only):**

Generate boundary tests based on the game type:

For **turn-based games** (card, board, strategy):
- Skip turn / pass every turn until game resolves
- Make invalid moves (click empty area, click opponent's pieces)
- Rapid click stress test

For **real-time games** (platformers, shooters, action):
- Hold all directions simultaneously
- Rapid key mashing
- Pause/unpause rapidly
- Move to screen boundaries

For **puzzle games**:
- Try invalid placements
- Fill board to maximum
- Undo repeatedly

For **all games** (universal boundary tests):
- Click rapidly in random areas (stress test)
- Click outside game area
- Resize browser window during gameplay
- Take screenshot at every detected game state
- Verify no WebGL context loss

**Each boundary test must:**
- Start from a known state (fresh page load → start game)
- Have a clear pass/fail criteria (no crash = pass)
- Take a screenshot on failure
- Have a reasonable timeout

### 3.3 Key Generation Principles

1. **All values from analysis** — coordinates, timings, state names, button
  labels all come from Phase 2. Never invent values.

2. **Adaptive complexity** — if Phase 2 found rich interaction data, generate
  detailed tests. If analysis was sparse, generate simpler exploration tests
  (random clicks, center clicks, screenshot-heavy).

3. **Graceful degradation** — if the game doesn't start the way we expect
  (wrong coordinates, different flow), the test should screenshot and fail
  with a clear message, not hang forever.

4. **Visual evidence priority** — screenshot at every meaningful moment.
  The report reader should be able to reconstruct the play session from
  screenshots alone.

### 3.4 Save

Ask: "May I write the test script to `tests/playwright/webgl-playtest-[date].spec.ts`?"

Write only after approval.

---

## Phase 4: Execute Tests

### 4.1 Run

```bash
npx playwright test tests/playwright/webgl-playtest-[date].spec.ts \
  --reporter=list 2>&1
```

Bash timeout: 300000ms (5 min).

If runner fails to start: "Playwright runner failed. Verify with `npx playwright --version`." → **STOP**

### 4.2 Collect Results

Parse runner output:
- Total / passed / failed / skipped counts
- Failed test names and error messages
- Screenshot paths from failures
- Execution time

---

## Phase 5: Generate Report

### 5.1 Compile

Combine:
- Phase 2 analysis (game type, states, interactions)
- Phase 4 results (pass/fail/skip)
- Screenshots (all captured during execution)
- Error messages and stack traces

### 5.2 Severity Classification

| Level | Criteria |
|-------|----------|
| **S1 — Critical** | Crash, WebGL context lost, blank screen, freeze |
| **S2 — Major** | Core mechanic broken, stuck state, can't start/play/end |
| **S3 — Moderate** | UI glitch, wrong visual feedback, animation break |
| **S4 — Minor** | Cosmetic, timing feel, non-blocking quirk |

### 5.3 Report Template

```markdown
# WebGL Playtest Report

> **Date**: [date]
> **Mode**: [quick | full]
> **URL**: [url]
> **Engine**: [detected engine]
> **Game Type**: [detected type]
> **Generated by**: /webgl-playtest

---

## Summary

| Metric | Value |
|--------|-------|
| Tests Run | [N] |
| Passed | [N] |
| Failed | [N] |
| Skipped | [N] |
| Bugs Found | [N] |
| Execution Time | [N]s |

---

## Game Analysis

[Insert the analysis report from Phase 2.6]

---

## Test Results

### Passed
| # | Test Name | Duration |
|---|-----------|----------|

### Failed
| # | Test Name | Error | Severity | Screenshot |
|---|-----------|-------|----------|------------|

### Skipped
| # | Test Name | Reason |
|---|-----------|--------|

---

## Bug Details

### BUG-001: [Title]
- **Severity**: S[N]
- **Test**: [test name]
- **Reproduction Steps**:
  1. Launch game at [URL]
  2. [step 2]
  3. [step 3]
- **Expected**: [what should happen]
- **Actual**: [what happened]
- **Screenshot**: `tests/playwright/screenshots/[date]/[file].png`

---

## Boundary Exploration

| Scenario | Result | Notes |
|----------|--------|-------|
| [scenario] | PASS/FAIL | [observation] |

---

## Recommendations

1. [Priority] [recommendation]

---

## Screenshots

| # | Name | Description | Path |
|---|------|-------------|------|
| 1 | 01-loaded | Initial load | [path] |
| 2 | 02-start-step-1 | After start | [path] |
| ... | ... | ... | ... |
```

### 5.4 Save

Ask: "May I write this report to `production/qa/webgl-playtest-[date].md`?"

Write only after approval.

After writing:
"Report saved. [N] tests, [N] passed, [N] failed.
[If bugs:] Review BUG-001..BUG-[N] for details and screenshots.
[If clean:] All tests passed. Run `/webgl-playtest full` for deeper testing."

---

## Collaborative Protocol

- **Never modify game source code** — read-only analysis + testing.
- **Never auto-fix bugs** — report with screenshots and repro steps.
- **Derive everything from source** — coordinates, timings, state names
  all come from Phase 2 analysis. Zero hardcoded game-specific values
  in this skill definition.
- **Ask when uncertain** — if source analysis can't determine how to start
  the game or what the player does, ask the user via AskUserQuestion.
  Do not guess.
- **Ask before writing** — Phase 3 and Phase 5 need explicit approval.
- **Stop on environment failure** — missing Playwright or offline server.
- **Screenshot everything** — visual evidence is the primary output.
- **Timeout safety** — every loop needs a guard against infinite execution.
- **Engine-agnostic** — works with Phaser, PixiJS, Three.js, Babylon.js,
  or raw WebGL canvas games. The analysis phase adapts to whatever it finds.
- **Full workflow** — analyze → generate → execute → report. Not just a
  script generator.
