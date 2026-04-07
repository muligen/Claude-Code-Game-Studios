# Skill 体系

73 个斜杠命令，按功能分为 12 个类别。在 Claude Code 中输入 `/` 即可调用。

---

## 引导与导航

| 命令 | 用途 |
|------|------|
| `/start` | 首次引导流程 — 询问项目状态，引导到正确的工作流 |
| `/help` | 上下文感知的"下一步做什么"— 读取当前阶段，给出建议 |
| `/project-stage-detect` | 完整项目审计 — 检测阶段、识别缺口、建议下一步 |
| `/setup-engine` | 配置引擎版本，检测知识盲区，填充版本参考文档 |
| `/onboard` | 为新贡献者或 Agent 生成上下文引导文档 |
| `/adopt` | 棕地项目审计 — 检查现有 GDD/ADR/Story 格式，生成迁移计划 |

---

## 游戏设计

| 命令 | 用途 |
|------|------|
| `/brainstorm` | 使用专业工作室方法引导创意（MDA、SDT、Bartle、动词优先） |
| `/map-systems` | 将概念分解为系统，映射依赖，确定设计优先级 |
| `/design-system` | 逐节引导编写单个系统的 GDD |
| `/quick-design` | 轻量设计规格 — 用于微调、小修改、小功能添加 |
| `/design-review` | 审查游戏设计文档的完整性和一致性 |
| `/review-all-gdds` | 跨 GDD 一致性和整体设计质量审查 |
| `/consistency-check` | 扫描所有 GDD 中的跨文档矛盾（相同实体不同数值等） |
| `/propagate-design-change` | GDD 修改后，查找受影响的 ADR 并生成影响报告 |

---

## UX 与界面设计

| 命令 | 用途 |
|------|------|
| `/ux-design` | 逐节引导编写 UX 规格（界面/流程、HUD、模式库） |
| `/ux-review` | 验证 UX 规格是否对齐 GDD、无障碍和模式合规 |

---

## 架构

| 命令 | 用途 |
|------|------|
| `/create-architecture` | 逐节引导编写主架构文档 |
| `/architecture-decision` | 创建架构决策记录（ADR） |
| `/architecture-review` | 审查所有 ADR 的完整性、依赖排序和 GDD 覆盖 |
| `/create-control-manifest` | 从已批准的 ADR 生成程序员规则清单 |

---

## Story 与 Sprint

| 命令 | 用途 |
|------|------|
| `/create-epics` | 将 GDD + ADR 转化为 Epic（每个架构模块一个） |
| `/create-stories` | 将单个 Epic 拆分为可实现的 Story 文件 |
| `/story-readiness` | 验证 Story 是否准备好被实现（READY/NEEDS WORK/BLOCKED） |
| `/dev-story` | 读取 Story 并实现 — 自动路由到正确的程序员 Agent |
| `/story-done` | 8 阶段完成审查；更新 Story 文件，提示下一个 Story |
| `/estimate` | 结构化工作量估算（复杂度、依赖、风险分解） |
| `/sprint-plan` | 生成或更新 Sprint 计划；初始化 sprint-status.yaml |
| `/sprint-status` | 30 行快速 Sprint 概览快照 |

---

## 审查与分析

| 命令 | 用途 |
|------|------|
| `/code-review` | 针对文件或变更集的架构级代码审查 |
| `/balance-check` | 分析游戏平衡数据、公式和配置，标记异常值 |
| `/asset-audit` | 审计素材命名规范、文件大小预算和管线合规 |
| `/content-audit` | 审计 GDD 指定的内容数量 vs 已实现内容 |
| `/scope-check` | 分析功能或 Sprint 范围是否超出原始计划 |
| `/perf-profile` | 结构化性能分析，定位瓶颈 |
| `/tech-debt` | 扫描、跟踪、优先排序和报告技术债 |
| `/gate-check` | 验证阶段间推进的准备度（PASS/CONCERNS/FAIL） |

---

## QA 与测试

| 命令 | 用途 |
|------|------|
| `/qa-plan` | 为 Sprint 或功能生成 QA 测试计划 |
| `/smoke-check` | 在 QA 接手前运行关键路径冒烟测试 |
| `/soak-test` | 生成长时间测试协议 |
| `/regression-suite` | 将测试覆盖映射到 GDD 关键路径，识别缺少回归测试的已修复缺陷 |
| `/test-setup` | 为项目引擎搭建测试框架和 CI/CD 管线 |
| `/test-helpers` | 生成引擎特定的测试辅助库 |
| `/test-evidence-review` | 审查测试文件和手动证据文档的质量 |
| `/test-flakiness` | 从 CI 日志检测不稳定测试 |
| `/skill-test` | 验证 Skill 文件的结构合规性和行为正确性 |

---

## 生产管理

| 命令 | 用途 |
|------|------|
| `/milestone-review` | 审查里程碑进度并生成状态报告 |
| `/retrospective` | 运行结构化 Sprint 或里程碑回顾 |
| `/bug-report` | 创建结构化缺陷报告 |
| `/bug-triage` | 读取所有开放缺陷，重新评估优先级和严重度 |
| `/reverse-document` | 从已有实现反向生成设计或架构文档 |
| `/playtest-report` | 生成结构化测试报告或分析现有测试笔记 |
| `/localize` | 本地化工作流：字符串提取、验证、翻译就绪 |

---

## 发布

| 命令 | 用途 |
|------|------|
| `/release-checklist` | 生成并验证发布前检查清单 |
| `/launch-checklist` | 完成跨部门的上线就绪验证 |
| `/changelog` | 从 git 提交和 Sprint 数据自动生成变更日志 |
| `/patch-notes` | 从 git 历史和内部数据生成面向玩家的补丁说明 |
| `/hotfix` | 紧急修复工作流（带审计跟踪，绕过正常 Sprint） |
| `/day-one-patch` | 首日补丁流程 |

---

## 创意与原型

| 命令 | 用途 |
|------|------|
| `/prototype` | 快速一次性原型验证机制（放宽标准，隔离工作区） |
| `/art-bible` | 创建美术圣经 — 概念确定后的视觉方向指南 |
| `/asset-spec` | 为指定系统生成素材规格 |

---

## 团队编排

| 命令 | 协调的 Agent |
|------|-------------|
| `/team-combat` | game-designer + gameplay-programmer + ai-programmer + technical-artist + sound-designer + qa-tester |
| `/team-narrative` | narrative-director + writer + world-builder + level-designer |
| `/team-ui` | ux-designer + ui-programmer + art-director + accessibility-specialist |
| `/team-release` | release-manager + qa-lead + devops-engineer + producer |
| `/team-polish` | performance-analyst + technical-artist + sound-designer + qa-tester |
| `/team-audio` | audio-director + sound-designer + technical-artist + gameplay-programmer |
| `/team-level` | level-designer + narrative-director + world-builder + art-director + systems-designer + qa-tester |
| `/team-live-ops` | live-ops-designer + economy-designer + community-manager + analytics-engineer |
| `/team-qa` | qa-lead + qa-tester + gameplay-programmer + producer |

---

## 自动化管线

| 命令 | 用途 |
|------|------|
| `/drive` | 项目自动巡航 — 从当前状态开始，逐步推进直到发布 |
| `/drive-init` | 从零到 Demo — 空项目到 Production 门禁通过 |
| `/drive-iterate` | 修改已有设计 — 自动分析影响、分类严重度、执行验证 |
| `/drive-add` | 添加新设计 — 完整的设计到实现验证管线 |

详见 [04-自动化管线](04-自动化管线.md)。

---

## Skill 维护

| 命令 | 用途 |
|------|------|
| `/skill-test` | 验证 Skill 文件结构合规（static 模式）或行为正确（behavioral 模式） |
| `/skill-improve` | 分析现有 Skill 并提出改进建议 |
