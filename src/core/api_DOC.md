# 无人机 API 文档 (Documentation for api.py)

**文件位置**: `src/core/api.py`
**功能**: 沙盒环境的接口层。这些方法 (`move`, `plant` 等) 可以在用户的 Python 脚本中直接调用。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **6-19** | `__init__` | 初始化无人机状态。`self.events` 队列是**无人机线程与 UI 主线程通信的唯一桥梁**。 |
| **20-24** | `_check` | **安全检查**。每次执行动作前都会调用。如果 `_stop_flag` 为真（用户点了 STOP），立刻调用 `sys.exit()` 终止脚本线程。此外，这里实现了 `time.sleep(DELAY)`，模拟机械运动的耗时。 |
| **25-41** | `move(direction)` | **移动逻辑**。支持 "North/South/West/East"。包含 `Wrap around` (地图环绕) 逻辑 (`nx % GRID_WIDTH`)。这让地图变成了“环形世界”。最后将移动事件推入 `self.events` 供 UI 渲染。 |
| **43-60** | `plant(crop_name)` | **种植逻辑**。从工厂获取类 -> 调用 `farm.plant_crop`。如果该格子已有作物，会先自动 `destroy_crop` (覆盖种植)。这是一种“宽容”的设计。 |
| **62-78** | `harvest()` | **收割逻辑**。尝试收割当前脚下的作物。如果是大型作物 (Size N)，获得的数量是 N*N。收成直接存入 `self.inventory` (内存字典)。 |
| **83-88** | `destroy()` | **销毁**。铲除当前格子的所有内容（不获得收益）。 |
| **90-91** | `log(msg)` | 对应 Python 里的 `print()`。脚本里的 `print()` 被重定向到这个方法，最终显示在游戏控制台中。 |

## 🛠️ 维护与扩展指南

### 如何添加新指令？
例如，想添加一个 `drone.water()`:
1.  在 `DroneAPI` 类中定义 `water(self)` 方法。
2.  在其中调用 `self._check()`。
3.  调用 `self.farm.water_crop(self.x, self.y)` (需要在 farm.py 中先实现它)。
4.  添加事件: `self.events.append({"type": "water", ...})`。
5.  在 `ide.py` 的渲染循环中处理 "water" 事件并播放动画。
