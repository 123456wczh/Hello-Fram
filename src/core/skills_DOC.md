# 技能系统文档 (Documentation for skills.py)

**文件位置**: `src/core/skills.py`
**功能**: 定义技能树结构、解锁条件及数据管理。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **1-13** | `SkillNode` | **数据结构**。每个技能节点包含 ID、名称、描述、花费 (`cost` 字典)、`parent_id` (前置技能) 以及用于在 UI 上绘制连线的坐标 (`x, y`)。 |
| **14-43** | `_init_skills` | **技能树配置**。这里硬编码了科技树结构。<br>`add_speed_1`: 根节点。<br>`unlock_pumpkin`: 左分支，解锁南瓜。<br>`unlock_sunflower`: 二级左分支，解锁向日葵。<br>**维护提示**：所有新技能都在这里添加。 |
| **47-63** | `can_unlock` | **条件判定**。检查三个条件：<br>1. 是否已解锁。<br>2. 库存资源是否足够 (`inventory.get(...) < amount`)。<br>3. 父节点是否已解锁 (`parent.unlocked`)。 |
| **65-75** | `unlock` | **执行解锁**。先扣除资源，再设置 `unlocked = True`。这一步不播放音效，音效在 UI 层 (`ide.py`) 调用此方法成功后播放。 |

## 🛠️ 维护与扩展指南

### 如何添加新技能？
1.  在 `_init_skills` 末尾调用 `self.add_skill(...)`。
2.  参数 `x, y` 是相对坐标（0-1），UI 会根据窗口大小自动缩放。建议 `(0.5, 0.5)` 为中心。
3.  **注意父子依赖**: 确保 `parent_id` 是已存在的 ID，否则会报错。

### 技能效果在哪里生效？
*   `skills.py` **只负责数据** (已解锁/未解锁)。
*   真正的效果实现散落在各处。例如 `speed_1` 的加速效果，实际上是在 `DroneAPI` 的 `move` 方法延迟计算中判断的 (目前可能尚未实装，需检查 `config.py` 或 `api.py`)。
*   解锁作物 (如 `unlock_pumpkin`) 的效果是在 UI 的 `SkillTreeWindow` 中被用户看到，用户随后便可编写代码种植。
