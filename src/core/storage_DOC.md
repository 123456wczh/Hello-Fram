# 存取档与文件管理文档 (Documentation for storage.py)

**文件位置**: `src/core/storage.py`
**功能**: 处理游戏状态 (`savegame.json`) 的序列化以及初始化用户脚本目录 (`user_scripts/`)。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **7-9** | `ensure_user_scripts_dir` | **初始化**。检查 `user_scripts` 文件夹是否存在，不存在则创建。这是 V4.1 版本引入的关键改动，将用户代码与系统存档分离。 |
| **12-33** | `save_game` | **保存**。参数接收 `farm` 和 `drone` 对象。先调用它们的 `to_dict()` 方法获取字典数据，然后合并保存到 JSON。**注意**：这里不再保存代码编辑器里的文本 (`code_text` 参数被废弃但保留了接口定义以兼容旧代码)。 |
| **36-58** | `load_game` | **读取**。从 JSON 读取数据并注入到传入的 `farm` 和 `drone` 对象中 (`load_from_data`)。如果文件不存在返回 None。 |

## 🛠️ 维护与扩展指南

### 存档里为什么没有用户代码？
*   **设计变更 (V4.1)**: 用户的 Python 脚本现在直接保存为 `.py` 文件在 `user_scripts/` 下，由 `CodeEditorWindow.save_to_disk` 负责。
*   `savegame.json` 只负责保存“游戏内资产” (金币、作物状态、已解锁技能)。
