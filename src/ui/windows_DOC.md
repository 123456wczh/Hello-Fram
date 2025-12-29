# UI 窗口组件文档 (Documentation for windows.py)

**文件位置**: `src/ui/windows.py`
**功能**: 定义所有悬浮窗口、弹窗和编辑器面板。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **14-45** | `BaseModal` | **弹窗基类**。所有窗口的父类。封装了 `pygame_gui.elements.UIWindow` 的创建、居中和显隐逻辑。避免了重复写 `manager=self.manager` 和 `rect` 计算。 |
| **47-275** | `CodeEditorWindow` | **核心编辑器**。<br>包含 `UITextBox` (代码区) 和 `RUN`/`SAVE`/`STOP` 按钮。<br>**高亮**: `_update_display` 中调用 `SyntaxHighlighter` 并加上光标 `|`。<br>**键盘处理**: 在 `handle_event` 中手动处理输入 (`K_BACKSPACE`, `K_RETURN` 等)，因为 pygame_gui 的文本框本身只支持 HTML 显示，不支持真正的可编程编辑，所以这里实现了一个**简易文本编辑器内核**。 |
| **276-324** | `CropDetailWindow` | **详情弹窗**。显示作物的大图标、价值与特殊能力介绍 (如南瓜的融合特性)。可拖拽。 |
| **327-404** | `CropGuideWindow` | **帮助文档**。农业数据库，显示所有已注册作物。使用 `UIScrollingContainer` 制作了滚动列表。动态从 `CROP_FACTORY` 读取数据，无需手动更新。 |
| **405-508** | `SkillTreeWindow` | **技能树窗口**。<br>**连线**: `_build_ui` 中使用 `pygame.draw.line` 在 `bg_surf` 上绘制技能依赖连线，然后贴到窗口背景上。<br>**按钮**: 根据 `x,y` 坐标动态生成按钮。 |
| **509-570** | `NewFileModal` | **新建文件对话框**。让用户输入文件名。会检查重名并加上 `.py` 后缀。 |
| **571-677** | `FileBrowserWindow` | **文件浏览器 (V4.1 重构)**。<br>**双栏设计**: 左边显示 `user_scripts/` (可读写)，右边显示 `src/examples/` (只读)。<br>**open_selected**: 根据选择打开文件。如果是 Example，会以只读模式打开（但目前代码里只是打印提示，逻辑上并未彻底禁止修改内存中的文本，只是不会保存回 src 目录）。 |

## 🛠️ 维护与扩展指南

### 如何修复 "代码编辑器输入卡顿"？
*   `CodeEditorWindow` 的 `handle_event` 是逐帧处理 `KEYDOWN` 的。Pygame 的 `key.set_repeat(500, 50)` (在 `ide.py` 设置) 决定了连按速度。如果卡顿，检查 `ide.py` 的渲染帧率。

### 如何给窗口添加关闭按钮回调？
*   pygame_gui 的窗口默认右上角有 X。当点击时会触发 `UI_WINDOW_CLOSE` 事件。
*   在 `ide.py` 的事件循环中捕获此事件并进行清理 (`win.destroy()`)。不要在 `windows.py` 里直接 destroy，否则主循环里的列表引用会报错。
