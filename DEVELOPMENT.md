# Architecture & Development Guidelines (架构与开发指南)

## 1. 技术栈选型 (Tech Stack)
* **主界面 UI (Frontend):** `CustomTkinter` (提供现代、暗黑风格的流畅桌面体验)。
* **代理 UI 引擎 (Proxy Engine):** `Gooey` (作为生成目标 EXE 的底层 UI 框架)。
* **代码生成器 (Code Generator):** Python 原生字符串模板 (F-strings / `string.Template`)。
* **编译器 (Compiler):** `PyInstaller` (以 `-F -w` 模式静默调用)。
* **`json_ingestor.py` (参数解析器):** 
  - 在主界面新增一个 Textbox (多行文本框)，用于接收用户粘贴的 JSON 字符串。
  - 包含 JSON 校验逻辑，清洗并自动映射为界面上的动态参数列表。

## 2. 核心模块划分 (Core Modules)
本项目采用严格的 MVC (Model-View-Controller) 解耦架构，以便于 AI 辅助开发：

* **`ui_manager.py` (视图层):**
  - 负责渲染主界面。
  - 包含动态参数列表组件 (支持增删改查参数项)。
  - 收集用户输入的所有配置数据 (JSON 格式)。
* **`code_generator.py` (逻辑层):**
  - 接收 UI 传来的 JSON 数据。
  - 注入预设的 `launcher_template.py` 模板。
  - 在系统的 Temp 目录下生成临时的 `proxy_launcher.py` 源码文件。
* **`build_engine.py` (执行层):**
  - 封装 `subprocess` 模块。
  - 在后台静默执行 `pyinstaller -F -w temp/proxy_launcher.py`。
  - 捕获编译日志并实时回传给 UI 界面的进度条。

## 3. IDE 氛围编程协议 (AI Copilot Protocol)
在后续使用 Trae/Cursor 开发时，请严格遵守以下 Prompt (提示词) 规范：
1. **分步构建:** 不要让 AI 一次性写完整个项目。先要求：“编写 `ui_manager.py` 的基础框架，包含路径选择和全局配置区”。
2. **接口先行:** 在让 AI 写生成器前，先定义好 UI 传递给生成器的数据结构 (Data Schema)。
3. **防御性编程:** 强制要求 AI 在 `build_engine.py` 中加入异常捕获机制，处理 PyInstaller 可能缺失或权限不足的问题。

## 4. Script-Pilot 标准传参 JSON 协议 (Data Schema)
AI 提取的参数必须严格符合以下 JSON 数组格式，以便 APP 解析：
```
[
  {
    "name": "--url", 
    "widget": "TextField",
    "help": "目标网址的详细说明", 
    "required": true, 
    "default": "https://"
  },
  {
    "name": "--input_file", 
    "widget": "FileChooser", 
    "help": "请选择要处理的 Excel 文件", 
    "required": true, 
    "default": ""
  }
]
```
(注：widget 支持的值包括：TextField, FileChooser, DirChooser, Dropdown)
