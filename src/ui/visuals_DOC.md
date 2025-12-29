# 视觉与特效系统文档 (Documentation for visuals.py)

**文件位置**: `src/ui/visuals.py`
**功能**: 负责游戏的所有资产加载（图片、音效）、粒子系统、以及补间动画 (`Tweening`) 逻辑。

## 📜 代码逐行解析

| 行号范围 | 代码内容 | 解析与说明 |
| :--- | :--- | :--- |
| **8-17** | `ease_out_quad` 等 | **缓动函数**。定义了动画变换的速度曲线。`ease_out_back` 会在结束时产生轻微的“回弹”效果，常用于无人机移动。 |
| **19-53** | `Tween` 类 | **补间执行器**。通过每一帧修改对象的属性值（如 `x`, `y`, `alpha`），实现平滑过渡。 |
| **56-109** | `Particle` 类 | **粒子单元**。管理单个粒子的寿命、速度、旋转和淡出效果。支持 `scale_fade`（死亡时逐渐变小）。 |
| **112-120** | `VisualManager` (Singleton) | **单例管理器**。保证全局只有一个资产库。通过 `__new__` 实现。 |
| **130-150** | `load_assets` | **图片加载**。扫描根目录 `assets/` 下的所有 `.png` 文件，并使用 `convert_alpha()` 优化性能。文件名去掉后缀即为索引 `Key`。 |
| **151-168** | `load_sounds` | **音效加载**。初始化 `pygame.mixer` 并扫描 `assets/sfx/`。 |
| **188-195** | `get_asset` | **资产检索**。提供安全访问。如果找不到图片，会返回一个 **品红色 (Magenta)** 的 32x32 方块，提示开发者资源缺失。 |
| **199-235** | `spawn_...` | **特效生成器**。提供快捷方法，如 `spawn_dust` (烟尘)、`spawn_spark` (火花)、`spawn_floating_text` (飘字，如 "+$100")。 |
| **242-256** | `update` & `draw` | **混合循环**。更新所有存活粒子的物理状态，并自动过滤掉已死亡的补间动画。 |

## 🛠️ 维护与扩展指南

### 如何添加一个新的音效？
1.  将 `.wav` 文件放入 `assets/sfx/` 目录。
2.  在代码中直接调用 `VisualManager.play_sound("文件名")`。

### 如何让无人机移动得更平滑？
*   在 `ide.py` 调用补间时，更换不同的缓动函数（Easing）。例如将 `ease_out_quad` 改为 `ease_out_back`。

### 性能优化建议
*   目前的粒子系统使用 `image.copy()` 来处理 Alpha 通道，这在粒子数量极多（>500个）时会影响 FPS。如果需要海量粒子，建议使用 `Surface.set_alpha` 结合 `dirty_rects` 或 `pygame.sprite.Group`。

### 为什么提示 "Asset dir not found"？
*   检查 `root_dir` 的计算（第 134 行）。它依赖于当前文件的位置。如果项目根目录结构发生变化，需要相应调整路径层级。
