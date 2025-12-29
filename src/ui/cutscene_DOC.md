# 剧情与向导系统文档 (Documentation for cutscene.py)

**文件位置**: `src/ui/cutscene.py`
**功能**: 管理游戏的开场动画、新手教程以及游戏中的 AI 辅助对话系统。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **5-28** | `DialogBox.__init__` | **对话框外观**。定义了位置 (`SCREEN_HEIGHT - 160`)、背景颜色（深色半透明）和青色 (`Cyan`) 边框。使用默认系统字体以增强兼容性。 |
| **38-52** | `DialogBox.update` | **打字机效果**。通过 `char_index` 逐帧增加字符。每 4 个字符触发一次 `blip` 音效。完成后显示 `[CLICK]` 提示。 |
| **54-93** | `DialogBox.draw` | **手工渲染**。由于对话框需要逐字显示、多行折行和发光边框，这里没有用 `pygame_gui`，而是直接用 Pygame 原生绘图函数实现，从而获得更细腻的动画感。 |
| **95-103** | `CutsceneManager` | **向导状态机**。持有 `ide` 引用以便检测游戏状态（如编辑器是否打开）。`triggers_enabled` 用于控制随机提示的开关。 |
| **104-115** | `trigger` | **事件监听器**。当无人机做出动作（如第一次收获 `first_harvest`）时，IDE 会调用此方法，从而触发相应的对话响应。 |
| **133-162** | `update` (状态检测) | **核心教学逻辑**。当状态为 `WAITING_ACTION` 时，会持续轮询游戏环境：<br>- `OPEN_EDITOR`: 检查 `ide.editor_windows` 长度。<br>- `RUN_CODE`: 检查无人机坐标是否发生变化。 |
| **167-217** | `next_step` | **剧本脚本**。硬编码了从 Step 1 (系统启动) 到 Step 15 (校准结束) 的所有文案和等待条件。 |

## 🛠️ 维护与扩展指南

### 如何添加一段新的剧情对话？
1.  **在 `next_step` 末尾添加分支**：
    ```python
    elif self.step == 16:
        self.dialog.show("BOSS", "You are doing great, Pilot.")
    ```
2.  **设置后续状态**：如果是单纯对话，`state` 保持为 `PLAYING`；如果是要求玩家操作，设置为 `WAITING_ACTION` 并定义 `wait_condition`。

### 如何修改打字速度？
*   修改 `DialogBox` 类中的 `self.typing_speed`。数值越大，文字出现越快。

### 为什么提示点击没反应？
*   检查 `handle_event`。为了让对话进行，必须在 `PLAYING` 状态且 `waiting_for_input` 为 True 时点击。如果对话还没打完字，点击是无效的（除非你实现了“点击立即完成打字”的逻辑）。
