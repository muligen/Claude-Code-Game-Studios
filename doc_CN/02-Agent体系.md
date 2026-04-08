# Agent 体系

50 个 Agent 按三级层次组织，每个负责一个专属领域。

## 层次结构

```
                        [用户]
                          |
          +---------------+---------------+
          |               |               |
  creative-director  technical-director  producer
          |               |               |
     +----+----+     lead-programmer  （协调所有）
     |    |    |          |
  game  art  narr   +----+----+----+----+----+
  designer dir ector |    |    |    |    |    |
     |         gp    ep   ai   net  tl   ui
  sys lvl eco
```

## 委派规则

1. **纵向委派**：领导 Agent 委派给部门主管，部门主管委派给专家，不跳层
2. **横向咨询**：同层 Agent 可互相咨询，但不做跨域决策
3. **冲突升级**：两方无法达成一致时，升级到共同上级
4. **禁止跨域修改**：Agent 不得修改非自己负责的文件

---

## Tier 1 — 领导层（Opus 模型）

| Agent | 职责 | 使用场景 |
|-------|------|---------|
| `creative-director` | 创意最高决策 | 愿景冲突、支柱矛盾、调性/方向、跨部门分歧裁决 |
| `technical-director` | 技术最高决策 | 架构决策、技术选型、性能策略、技术风险 |
| `producer` | 生产管理 | Sprint 规划、里程碑跟踪、风险管理、跨部门协调 |

---

## Tier 2 — 部门主管（Sonnet 模型）

| Agent | 职责 |
|-------|------|
| `game-designer` | 游戏设计：机制、系统、进度、经济、平衡 |
| `lead-programmer` | 代码架构：系统设计、代码审查、API 设计、重构 |
| `art-director` | 视觉方向：风格指南、美术圣经、素材标准、UI/UX 视觉设计 |
| `audio-director` | 音频方向：音乐方向、音色调性、音频实现策略 |
| `narrative-director` | 故事与叙事：故事线、世界观、角色设计、对话策略 |
| `qa-lead` | 质量保障：测试策略、缺陷分流、发布就绪、回归计划 |
| `release-manager` | 发布管线：构建管理、版本号、变更日志、部署、回滚 |
| `localization-lead` | 国际化：字符串外化、翻译管线、区域测试 |

---

## Tier 3 — 专家（Sonnet/Haiku 模型）

### 设计类

| Agent | 模型 | 职责 |
|-------|------|------|
| `systems-designer` | Sonnet | 具体机制设计、公式、交互矩阵 |
| `level-designer` | Sonnet | 关卡布局、节奏、遭遇设计、空间谜题 |
| `economy-designer` | Sonnet | 资源经济、掉落表、进度曲线、市场平衡 |
| `world-builder` | Sonnet | 世界规则、势力设计、历史、地理、生态 |

### 编程类

| Agent | 模型 | 职责 |
|-------|------|------|
| `gameplay-programmer` | Sonnet | 功能实现、玩法系统代码 |
| `engine-programmer` | Sonnet | 核心引擎、渲染、物理、内存管理 |
| `ai-programmer` | Sonnet | 行为树、寻路、NPC 逻辑、状态机 |
| `network-programmer` | Sonnet | 网络代码、复制、延迟补偿、匹配 |
| `tools-programmer` | Sonnet | 编辑器扩展、管线工具、调试工具 |
| `ui-programmer` | Sonnet | UI 框架、界面、数据绑定 |
| `technical-artist` | Sonnet | 着色器、VFX、渲染优化、美术管线工具 |

### 内容创作类

| Agent | 模型 | 职责 |
|-------|------|------|
| `writer` | Sonnet | 对话、故事条目、物品描述、环境文本 |
| `sound-designer` | Haiku | 音效规格、音频事件列表、混音参数 |
| `art-producer` | Sonnet | 根据规格调用 API 生成实际美术素材 |

### 质量与运维类

| Agent | 模型 | 职责 |
|-------|------|------|
| `qa-tester` | Haiku | 测试用例、缺陷报告、测试清单 |
| `performance-analyst` | Sonnet | 性能分析、瓶颈定位、优化建议 |
| `devops-engineer` | Haiku | CI/CD、构建脚本、版本控制 |
| `security-engineer` | Sonnet | 反作弊、漏洞防护、数据加密 |
| `analytics-engineer` | Sonnet | 遥测、仪表盘、A/B 测试 |

### 其他专家

| Agent | 模型 | 职责 |
|-------|------|------|
| `prototyper` | Sonnet | 快速原型、机制验证、可行性测试 |
| `ux-designer` | Sonnet | 用户流程、交互设计、无障碍、输入 |
| `accessibility-specialist` | Haiku | WCAG 合规、色盲模式、按键重映射、文字缩放 |
| `live-ops-designer` | Sonnet | 赛季、活动、战斗通行证、留存、在线经济 |
| `community-manager` | Haiku | 补丁说明、玩家反馈、危机沟通 |

---

## 引擎专家

### Godot 4

| Agent | 职责 |
|-------|------|
| `godot-specialist` | Godot 总管：GDScript vs C# vs GDExtension 决策、节点/场景架构、信号、资源 |
| `godot-gdscript-specialist` | 静态类型、设计模式、信号架构、协程、性能 |
| `godot-shader-specialist` | Godot 着色语言、可视化着色器、粒子、后处理 |
| `godot-gdextension-specialist` | C++/Rust 绑定、原生性能、自定义节点、构建系统 |

### Unity

| Agent | 职责 |
|-------|------|
| `unity-specialist` | Unity 总管：MonoBehaviour vs DOTS、Addressables、URP/HDRP |
| `unity-dots-specialist` | ECS 架构、Jobs、Burst 编译器、混合渲染 |
| `unity-shader-specialist` | Shader Graph、VFX Graph、SRP 定制、后处理 |
| `unity-addressables-specialist` | Addressable 分组、异步加载、内存管理、CDN |
| `unity-ui-specialist` | UI Toolkit、UGUI Canvas、数据绑定、跨平台输入 |

---

## 升级路径

| 情况 | 升级到 |
|------|--------|
| 设计师对机制有分歧 | `game-designer` |
| 设计与叙事冲突 | `creative-director` |
| 设计与技术可行性冲突 | `producer` → `creative-director` + `technical-director` |
| 代码架构分歧 | `technical-director` |
| 跨系统代码冲突 | `lead-programmer` → `technical-director` |
| 范围超出产能 | `producer` → `creative-director` 裁剪 |
| 性能预算违规 | `performance-analyst` 标记 → `technical-director` 决策 |
