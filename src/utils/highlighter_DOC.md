# 语法高亮系统文档 (Documentation for highlighter.py)

**文件位置**: `src/utils/highlighter.py`
**功能**: 将原始 Python 代码转换为 `pygame_gui` 可解析的 HTML 标签，实现代码编辑器的语法高亮。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **5-8** | `SyntaxHighlighter.__init__` | **初始化转换器**。使用 `pygments` 库。`lexer` 设置为 Python 语言，`formatter` 设置为 HTML 格式。`noclasses=True` 是关键，因为它将样式直接写入 HTML 标签（Inline Style），这符合 `pygame_gui` 的需求。 |
| **18-31** | `highlight` (提取内容) | **格式剥离**。`pygments` 默认会生成一个完整的 `<div>` 和 `<pre>` 包装。代码通过 `find` 和索引截取，只保留中间的核心代码内容。 |
| **37-42** | `replace("\n", "<br>")` | **换行符转换**。Pygame 的 HTML 渲染器不支持原生 `\n`，必须手动转换为 `<br>` 标签。 |
| **55-61** | `color_replacer` & `re.sub` | **标签转换 (核心黑科技)**。`pygments` 生成的是标签如 `<span style="color: #XYZ">`，但 `pygame_gui` 只认识 `<font color='#XYZ'>`。这里使用正则表达式进行深度转换。 |
| **65-67** | `while "<span" in ...` | **递归清洗**。清除所有残留的 `<span>` 标签，确保没有任何 `pygame_gui` 不认识的标签干扰渲染，防止界面出现乱码或空白。 |
| **76** | `font face='Consolas'` | **字体强制渲染**。将所有内容包裹在 `Consolas` 字体中。如果玩家系统没有此字体，Pygame 会自动退回到默认等宽字体。 |

## 🛠️ 维护与扩展指南

### 如何更换高亮配色方案？
*   修改 `__init__` 中的 `style_name`。常见的方案有 `monokai`, `colorful`, `autumn`, `friendly` 等。

### 为什么某些代码变色不正确？
*   本组件依赖于正则表达式 (`re.sub`)。如果代码中包含复杂的嵌套 HTML 注释，可能会干扰正则判定。在这种情况下，可以考虑编写一个更严谨的 HTML 解析循环，或者为 `pygments` 编写一个自定义的 Formatter。

### 性能提醒
*   正则表达式处理在大规模（超过 2000 行）文本时会产生毫秒级的延迟。由于编辑器窗口较小，目前的实时处理性能是绰绰有余的。但在处理超大文件时，建议仅对**可见区域**进行高亮计算。
