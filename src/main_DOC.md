# 主程序入口文档 (Documentation for main.py)

**文件位置**: `src/main.py`
**功能**: 游戏的启动入口。负责初始化环境并启动主循环。

## 📜 代码逐行解析

| 行号 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| 1-2 | `import sys`, `import os` | 导入系统标准库，用于设置 Python 路径。 |
| 4-5 | `sys.path.append(...)` | **关键配置**：将项目的根目录添加到 `sys.path`。这确保了无论你在哪里运行脚本 (如 `python src/main.py` 或 `python main.py`)，Python 都能正确识别 `src.ui`, `src.core` 等包。 |
| 7 | `from src.ui.ide import GameIDE` | 从 UI 层导入主游戏类 `GameIDE`。这是整个游戏的核心控制器。 |
| 9 | `if __name__ == "__main__":` | 标准 Python 入口保护，防止模块被导入时意外执行。 |
| 10 | `app = GameIDE()` | 实例化游戏对象。这一步会初始化 Pygame, 加载资源, 生成农场数据等。 |
| 11 | `app.run()` | 启动游戏主循环 (`while True`)。程序将阻塞在此直到游戏关闭。 |

## 🛠️ 维护指南

*   **极少修改**：除非你需要引入全局的异常捕获机制，或者修改启动参数（如命令行参数解析），否则不需要改动此文件。
*   **启动方式**：建议在根目录下运行 `python src/main.py`。
