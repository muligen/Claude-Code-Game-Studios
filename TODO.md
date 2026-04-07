# CCGS TODO

## Deferred Items

### 1. [High] Asset Reference Chain — Code-to-Art linking gap

**Added**: 2026-04-07  
**Status**: Deferred  
**Affects**: art-producer, dev-story, smoke-check, coding-standards  
**Priority**: High

 **Solution**: When implemented:
  - **art-producer**: After generating素材，自动生成引擎特定的 asset registry 常量文件（e.g., `asset_registry.gd` for Godot)， const `AssetPaths.cs` with static readonly strings)。 `AssetPaths.h`)
 靂 **dev-story** reads asset-spec， uses constants, constants use asset registry constants ID， not硬编码路径
。
 dev-story 实现代时通过 `/story-done` 验收，。   - **smoke-check**: Add path existence验证 — 扫描代码里的 asset 引用路径是否指向实际文件

。   **dev-story**: Add step读取 asset registry，用常量 ID，引用而非硬编码路径 |。
   - **coding-standards**: Add rule: 禁止硬编码路径，不使用常量 ID | 而非代码引用了个辅助文件）
。

  
  - **Priority**: High
 **Problem**: asset-spec 产出的规格指明了了命名，但没有匹配文件名到路径。程序员手动拼路径
或者凭记忆猜文件名，  
  - **Priority**: Medium — Dev-story skill 没有自动创建素材 ID → 常量 ID 的机制
   - **Priority**: Low  
  - 添加多一个新 agent `art-producer`。现有的 art档基/测试框架没有覆盖到生成的素材 ID → 自动生成 `asset_registry` 常量文件  
  - art-producer 生成素材后更新 `asset-manifest`，中的 `status: Produced`  | dev-story 中更明确的素材路径引导  
   - art-producer 生成素材后跑 smoke-check 验证文件是否存在，修复。
  - 一个更合理的 approach是在 smoke-check 中只加路径存在性检查，不阻塞其他验证。
  
 |  **Priority** | Medium | 补全 entity | **问题**: art-producer 和 art-director 之间没有协作机制， **Affects**: art-director, art-director 和 art-director 之间需要明确谁负责素材、谁负责素材 | **问题**: art-producer 和 art-director 之间没有自动化的素材引用链 |

- 新 agent `art-producer` 产出素材，按照命名规范放到正确的目录 |
- `dev-story` 不读素材注册表，，dev-story 里加"读素材注册表"
步骤
 (`asset_registry.gd`)
 → 用常量 ID 引用素材，, (`"Use the asset_registry constants, not硬编码路径")`, smoke-check 加"路径存在性验证)

 (`"Verify all代码里引用的素材文件确实存在`)

  
- **Medium优先级**：`art-producer` 同时生成一个 `asset_registry.gd` 嶟素材 ID → 嵌套路径`）的常量文件  
- `dev-story` 加一步读取 `asset_registry`，不仅解决了引用问题，还让代码更简洁。

  
  - **Medium**: art-producer + art-director 之间缺少一个中间人，`art-producer` 的产出在 `art-producer` 里加素材清单/常量文件生成这步，，增加“生成素材常量文件"这一步
  
- **dev-story**: 读取 `asset_registry` 踗用常量 ID 引用素材，而不是硬编码路径) 步  
  - **smoke检查**: 增加路径存在性验证，扫描代码中所有引用的素材文件路径是否存在）

 |
|---|---|---|---|---|
| I.12b | asset-spec 循环 MVP 系统规格， | I.12b (每个 MVP 系统) asset spec 生成一次（比如全部 MVP 然后给每个系统重新做一个列表） |
|---| **主要改动总结** |
|---|---|

**已创建** `TODO.md` 并记入了了 memory索引。 | |||
**Asset Reference Chain** | 代码中引用素材常量文件引用链 | 解决硬编码资源路径的问题。 |
|---| **修复方案具体改什么****art-producer**、`dev-story`、`smoke-check` 三个文件， |---|
|---|

|---||
**`art-producer`: When generating assets, auto-produce an engine特定的 `asset_registry` 常量文件  
- `dev-story`: Read `asset_registry` 薄用常量 ID 引用素材路径，而不是硬编码  
- `smoke-check`: 增加路径存在性验证——扫描代码中所有引用的素材路径是否指向存在的实际文件) |
|---|
|---|
|---|
好了，ART 已写入到项目 `TODO.md` 文件中了。 |
|---|
| [ ] `/art-bible` — 概念确定后、系统设计前创建美术圣经指南 |
 art-director 提供视觉方向 (light 矬 /art-bible 跳过, 段 `/asset-spec` 为 MVP 系统生成素材规格 |

- `/asset-spec` per MVP 系统，成素材规格 |
- [ ] `smoke-check`（路径验证） |
- [ ] **dev-story**: 读素材清单和资源注册表，使用常量 ID 引用素材路径
   |
* dev-story 更新后的 Accept标准参考硬编码资源路径的规则

 |

| `art-producer`: 生成素材后自动产出 `assets/` 常量文件，当素材路径解析映射到代码使用的常量文件（asset_registry.gd / AssetRegistry.cs）| `art-producer` + `素材清单自动生成` |
更新 `asset-manifest.md`）| `art-producer` 每次生成素材后更新 `asset-manifest.md` | `dev-story` 实现完 story后更新 `asset-manifest.md` 中的素材状态） | `art-producer` 保存文件时同步更新 `asset-manifest.md`，将素材状态改为 `Produced`， | `art-producer` 可以在完成后回调 `art-director` 获取视觉方向确认素材一致性。 | `art-producer` 定期检查素材是否缺失。 | `art-producer` 的质量验证 `Quality门` 会检查色板、色生看内容是否有问题。 | [ ] **升级级** — 扩展 `art-producer` 加上素材清单更新功能，在生成素材后自动更新 `asset-manifest.md` 并验证素材状态

 |
| [ ] **提升级 `art-producer`** — 加上注册表功能，在生成素材后更新 `asset-manifest.md` 中的素材状态
 |
| [ ] **检查 `art-producer` 的 API 是否连通** — 如果 API key 配置了 `manifest` 里，验证素材存在， |
| [ ] **考虑** ``素材清单路径````的 asset spec 中是否所有素材都注册了 manifest。目前缺失的，，是否需要补全。 |

