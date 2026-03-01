# Windows-MCP-Improve

基于 [CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP) 改进，主要解决了**鼠标点击不准确**和**中文输入失败**的问题。

## 改进内容

### 1. 坐标系统重构：0-1000 归一化坐标

**原项目问题**：使用像素坐标 + 截图缩放（如 2560×1440 缩小到 1920×1080），缩放/反缩放过程中误差被放大，导致鼠标点击位置偏移。

**改进方案**：采用 0-1000 归一化坐标系（参考 [qwen_autogui](https://github.com/tech-shrimp/qwen_autogui) 的做法）：
- `(0, 0)` = 屏幕左上角，`(1000, 1000)` = 屏幕右下角
- 元素列表中的坐标自动转换为 0-1000 空间
- Click/Move/Type/Scroll 等工具自动将 0-1000 反归一化为物理像素坐标
- 与 qwen3.5-plus 等多模态模型的视觉坐标估算能力更匹配

### 2. 鼠标点击修复：SetCursorPos + 相对模式

**原项目问题**：`mouse_event` 使用绝对坐标模式（`MOUSEEVENTF_ABSOLUTE`）进行坐标归一化，在不同 DPI 和多显示器配置下经常出现偏移。

**改进方案**：
- 先用 `SetCursorPos(x, y)` 精确移动光标（该 API 在所有 Windows 配置下都可靠）
- 再用 `mouse_event` 的相对模式（dx=0, dy=0）触发点击事件
- 完全绕过了 `mouse_event` 不可靠的绝对坐标归一化

### 3. 中文输入支持

**原项目问题**：`Type` 工具通过 `SendKeys`（`KEYEVENTF_UNICODE`）逐字符发送，在中文 IME 环境和微信等应用中经常失败。

**改进方案**：
- 检测到非 ASCII 文本时，自动切换为**剪贴板粘贴**方式（保存 → 设置剪贴板 → Ctrl+V → 恢复原剪贴板）
- 纯 ASCII 文本仍使用 `SendKeys`（效率更高）

### 4. 截图注解增强：坐标锚点

**原项目问题**：截图上的元素标注只显示索引号（如 `5`），对模型估算未标注元素的坐标没有帮助。

**改进方案**：
- 标注标签显示索引 + 0-1000 坐标（如 `5(156,208)`）
- 已标注元素成为"坐标锚点"，帮助模型通过临近参考更准确地估算未标注元素的位置

### 5. 参数解析增强

**原项目问题**：部分 MCP 客户端传递的 `loc` 参数是字符串格式（如 `"[200, 300]"`），导致类型错误。

**改进方案**：
- 添加 `_parse_loc` / `_parse_locs` 函数，支持 JSON 字符串、逗号分隔、空格分隔等多种格式
- 所有接受坐标参数的工具都经过统一解析

### 6. 其他改进

- 移除截图 padding（消除标注导致的系统性坐标偏移）
- DPI 感知初始化（`SetProcessDpiAwareness(PerMonitorDpiAware)`）
- 虚拟屏幕偏移处理（支持多显示器配置）
- Snapshot 默认开启截图（`use_vision=True`）
- 输出中添加坐标系统说明，引导模型正确使用坐标

## 安装使用

### 前置条件

- Windows 10/11
- Python 3.13+
- [UV 包管理器](https://github.com/astral-sh/uv)

### 从源码运行

```bash
git clone https://github.com/swx338/windows-MCP-improve.git
cd windows-MCP-improve
uv sync
uv run windows-mcp
```

### 在 MCP 客户端中配置

以 OpenCode 为例，在配置文件中添加：

```json
{
  "mcp": {
    "windows-mcp": {
      "type": "local",
      "command": ["uv", "--directory", "<项目路径>", "run", "windows-mcp"],
      "enabled": true,
      "environment": {
        "ANONYMIZED_TELEMETRY": "false"
      }
    }
  }
}
```

其他 MCP 客户端（Claude Desktop、Cursor、Gemini CLI 等）的配置方式类似，参考原项目文档。

## MCP 工具列表

| 工具 | 功能 |
|------|------|
| **Snapshot** | 截取桌面状态：窗口列表、交互元素（0-1000 坐标）、截图 |
| **Click** | 鼠标点击（左/右/中键，单击/双击/悬停） |
| **Type** | 文本输入（支持中文，支持清除、回车） |
| **Move** | 移动鼠标 / 拖拽 |
| **Scroll** | 滚动（垂直/水平） |
| **Shortcut** | 键盘快捷键 |
| **App** | 启动/切换/调整窗口 |
| **PowerShell** | 执行 PowerShell 命令 |
| **FileSystem** | 文件操作（读/写/复制/移动/删除/搜索） |
| **Scrape** | 网页内容抓取 |
| **Clipboard** | 剪贴板读写 |
| **Process** | 进程管理 |
| **SystemInfo** | 系统信息 |
| **Notification** | 桌面通知 |
| **MultiSelect** | 批量选择 |
| **MultiEdit** | 批量输入 |
| **LockScreen** | 锁屏 |
| **Registry** | 注册表操作 |

## 致谢

- 原项目：[CursorTouch/Windows-MCP](https://github.com/CursorTouch/Windows-MCP)
- 坐标系统参考：[qwen_autogui](https://github.com/tech-shrimp/qwen_autogui) 的 0-1000 归一化方案

## 许可证

本项目基于原项目的 [MIT 许可证](LICENSE.md) 进行分发。
