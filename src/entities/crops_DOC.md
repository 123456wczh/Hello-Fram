# 作物实体定义文档 (Documentation for crops.py)

**文件位置**: `src/entities/crops.py`
**功能**: 定义所有作物的属性（生长时间、价值、特殊逻辑）以及作物工厂 (`CROP_FACTORY`)。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **2-30** | `Crop` 基类 | 定义通用属性：<br>`max_growth`: 成熟所需秒数。<br>`value`: 基础售价。<br>`is_ready`: 属性，判断 `current_growth >= max_growth`。<br>`to_dict`: 序列化基础数据。 |
| **32-58** | `OccupiedSlot` | **占位格**。当生成大型作物 (如 2x2 南瓜) 时，右下角的 3 个格子会变成这个对象。它的 `is_ready` 和 `grow` 等属性都全部委托 (`delegate`) 给 `self.parent` (那个真正的大型作物)。 |
| **60-65** | `Carrot` | **胡萝卜**。最基础的作物。3秒成熟，价值10。无特殊逻辑。 |
| **66-114** | `Pumpkin` | **南瓜 (核心特色)**。最复杂的实体。<br>**特殊属性**: `level` (等级/尺寸), `is_rotten` (是否腐烂), `fate_checked` (是否已判定过腐烂)。<br>**动态价值**: `update_stats` 根据尺寸的平方 (`level * level`) 和等级计算指数级回报。<br>**腐烂逻辑 (Fate RotCheck)**: 在 `grow()` 中，一旦成熟 (`is_ready` 刚变为 True)，立即执行一次 20% 概率的腐烂判定 (`make_rotten`)。腐烂后价值归零。 |
| **115-119** | `Blueberry` | **蓝莓**。5秒成熟，价值30。 |
| **120-124** | `Sunflower` | **向日葵**。8秒成熟，价值50。后续可能加入净化污染的机制。 |
| **126-131** | `CROP_FACTORY` | **工厂字典**。API 通过字符串 `"pumpkin"` 在这里查找对应的类 `Pumpkin`。**所有新作物必须注册到这里**。 |

## 🛠️ 维护与扩展指南

### 如何添加新作物 "Tomato"？
1.  **复制模板**：复制 `Blueberry` 类，改名为 `Tomato`。
2.  **调整参数**：`super().__init__("Tomato", 6.0, 40)` (6秒成熟, 价值40)。
3.  **特殊能力**？如果西红柿有特殊能力（例如：只能种在湿润的一排），重写 `grow(dt)` 添加逻辑。
4.  **注册**：在文件末尾 `CROP_FACTORY` 添加 `"tomato": Tomato`。
