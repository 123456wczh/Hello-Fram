# 主控逻辑文档 (Documentation for ide.py)

**文件位置**: `src/ui/ide.py`
**功能**: 游戏的“大脑”。负责主游戏循环 (`Game Loop`)、输入事件分发、代码执行线程管理以及 UI 整合。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **24-90** | `__init__` | **初始化**。<br>1. 启动 Pygame。<br>2. 初始化 `UIManager` (UI管理器, 加载 `ui_theme.json`)。<br>3. 实例化核心对象：`Farm`, `DroneAPI`, `SkillManager`。<br>4. 初始化子窗口 (`editor_windows`, `windows` 字典)。<br>5. 预加载默认脚本 (`main.py`, `utils.py`) 并为每个生成一个 `CodeEditorWindow`。 |
| **92-118** | `run_user_code` | **代码执行器 (Sandbox)**。<br>1. 如果已有线程在跑，先通过 `stop_flag` 停止它。<br>2. 创建新线程 `target`。<br>3. **关键**: 使用 `exec(code, env)` 安全执行用户代码。`env` 字典定义了用户能访问的变量 (`drone`, `time`, `print`)。<br>这是将 Python 解释器嵌入游戏的核心机制。 |
| **120-182** | `start_demo` | **演示模式**。硬编码了一段 "Tactical Agriculture" 脚本字符串，并自动打开一个编辑器窗口运行它。用于新手引导最后的 showcase。 |
| **183-227** | `_init_ui_elements` | **UI 布局**。创建屏幕右上角的系统按钮 (`FILES`, `+`, `SAVE`, `LOAD` 等)。计算 `start_x` 以确保按钮右对齐。 |
| **267-293** | `process_drone_events` | **事件同步**。无人机线程 (`target`) 产生事件存入 `drone.events` 队列。主线程 (`run`) 在每一帧调用此方法，从队列取出事件并播放对应的动画 (`Tween`) 或音效。这解决了多线程渲染冲突问题。 |
| **294-374** | `draw_game_area` | **渲染循环**。<br>1. `window.fill`: 清屏。<br>2. 绘制网格线和地板贴图。<br>3. 绘制作物 (`Farm.grid`)。如果是大型南瓜 (`scale > 1`)，会绘制黄色边框。<br>4. 绘制无人机和 HUD 文字。 |
| **389-624** | `run` (主循环) | **游戏心脏** (`while self.running`)。<br>**事件处理**: <br>- `ui_manager.process_events`: 让 UI 响应鼠标。<br>- `cutscene_mgr.handle_event`: 剧情触发。<br>- `UI_BUTTON_PRESSED`: 处理所有按钮点击 (保存、运行、打开弹窗)。<br>- **Aux Windows**: (`self.aux_windows`) 确保弹窗也能收到事件。<br>**更新**: `farm.update(dt)`, `ui_manager.update(dt)`.<br>**绘制**: `draw_game_area()`, `ui_manager.draw_ui()`. |

## 🛠️ 维护与扩展指南

### 如何添加一个新的全局按钮？
1.  **定义应**: 在 `_init_ui_elements` 中创建 `self.btn_myfeature = UIButton(...)`。
2.  **布局**: 调整 `total_w` 和 `start_x` 计算逻辑，为新按钮腾出空间。
3.  **响应**: 在 `run()` 方法的 `UI_BUTTON_PRESSED` 里的 **Part 2 (System Buttons)** 区域 (约 506 行后) 添加:
    ```python
    elif event.ui_element == self.btn_myfeature:
        self.print_to_console("Feature clicked!")
    ```

### 为什么按键没反应？
*   **常见坑点**: 如果是新加的弹窗 (`BaseModal` 子类)，必须在创建时加入 `self.aux_windows.append(win)`。主循环只会把事件分发给 `editor_windows` 和 `aux_windows` 列表里的对象。

### 多线程安全
*   不要在 `run_user_code` 的线程里直接调用 `pygame` 绘图函数！
*   正确做法：在线程里修改数据 (`drone.x`) 或推入事件 (`drone.events`)，让主线程在 `process_drone_events` 里更新画面。
