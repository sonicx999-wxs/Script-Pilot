# Changelog

所有重要的项目版本更新将在此文件中记录。

## [0.3.0] - 2026-05-05

### 🆕 新增功能

- **脚本分析器 (Script Analyzer)**
  - 新增 `core/analyzer.py` 模块，实现脚本特征检测
  - 支持检测 `argparse`、`GooeyParser`、`click`、`sys.argv` 等命令行参数特征
  - 支持检测 `input()`、`sys.stdin.read` 等交互式特征
  - 根据分析结果智能推荐生成模式（gooey/pyw/lite_console）

- **智能分流建议系统**
  - 在 UI 中实现实时脚本分析和推荐模式显示
  - 推荐徽章自动显示在对应的选项前方（绿色背景白色文字）
  - 支持置信度计算，仅在置信度 > 60% 时显示推荐

- **Tabview UI 重构**
  - 右侧面板重构为三个标签页：参数配置、源码预览、运行日志
  - 源码预览支持 Pygments 语法高亮（需安装 pygments）
  - 运行日志支持详细模式（Verbose Mode）开关

- **实时编译日志管道**
  - `build_exe()` 支持 `log_callback` 参数，实现实时日志回传
  - 进度条随编译进度平滑呼吸动画（每5行日志步进一次）
  - 详细日志以浅灰色显示，关键节点使用彩色分级显示

- **脚本哈希与深度历史记录**
  - 使用 MD5 哈希识别脚本（仅读取前 1MB）
  - 自动关联历史 JSON 参数配置
  - 支持撤销清空和手动清空操作

### 🔧 功能改进

- **UI 布局优化**
  - 支持窗口动态缩放，设置最小尺寸 800x600
  - 左右面板宽度锁定（左侧 400px，右侧 480px），消除布局抖动
  - 底部按钮加长至 320px，提升视觉重心

- **非阻塞进程输出读取**
  - 使用 `select.select()` 替代阻塞式 `readline()`
  - 设置 0.1 秒超时，确保 Windows 兼容性
  - 避免进程输出缓冲区导致的阻塞问题

- **详细日志控制**
  - 添加 Verbose 开关控制编译日志详细程度
  - 开关状态持久化到 `script_pilot_history.json`
  - 即使关闭详细日志，进度条仍能正常呼吸

### 🐛 问题修复

- **徽章显示逻辑修复**
  - 修复 `gooey` 推荐模式下徽章不显示的问题
  - 修复单选框未自动选中推荐模式的问题
  - 徽章仅受脚本分析结果控制，不受手动点击影响

- **ttk 控件兼容性修复**
  - 替换所有 `ttk.Label`、`ttk.Button`、`ttk.Entry` 为标准 `tk` 控件
  - 修复 `ttk.Label` 不支持 `-fg` 选项的问题
  - 确保所有控件使用统一的背景色 `#f8f9fa`

- **进度条显隐控制**
  - 初始状态 `pack_forget()` 隐藏
  - 仅在 exe 模式生成时显示
  - 生成完成后立即隐藏

---

## [0.2.0] - 2026-05-05

### 🆕 新增功能

- **极轻量级 .pyw 启动器生成**
  - 新增 `build_pyw()` 方法，可瞬间生成单文件 `.pyw` 智能启动器
  - 无需 PyInstaller 编译，生成的启动器仅有 ~2MB
  - 支持零编译热更新，修改底层 `.py` 源码后直接保存即可

- **原生可视化自举注入 (Visual Bootstrapping)**
  - 重写自举注入模块，首次运行自动检测并安装 Gooey 依赖
  - 引入基于 `tkinter.ttk` 的多线程异步进度条界面
  - 提供友好的中文加载提示，防止用户困惑

- **Lite-Terminal 极简交互控制台**
  - 新增 `generate_lite_console_code()` 函数，生成基于原生 tkinter 的交互控制台
  - 纯原生实现，零外部依赖，生成的启动器约 12KB
  - 支持实时输入输出交互，底部 Entry 绑定回车键发送命令
  - 使用 `queue.Queue` 实现线程安全的输出更新
  - 包含高分屏适配：`ctypes.windll.shcore.SetProcessDpiAwareness(1)`
  - UI 风格：背景色 `#f8f9fa`，边框色 `#adb5bd`，字体 `Consolas 10`

- **启动器名称自动生成**
  - 选择目标脚本后自动生成启动器名称（格式：`[脚本名称]脚本的启动器`）
  - 支持中文、下划线、连字符等各种文件名

### 🔧 功能改进

- **增强的路径处理逻辑**
  - 使用 `os.path.dirname()` + `os.path.join()` 替代脆弱的字符串替换
  - 提升了 venv 路径和 pythonw.exe 路径解析的健壮性
  - 支持各种不同命名的虚拟环境路径

- **stdout/stderr 重定向优化**
  - 改进了 PyInstaller windowed 模式下的输出流处理
  - 避免了 Gooey 因 sys.stdout 为 None 导致的死循环问题
  - 确保 UTF-8 编码输出，防止中文乱码

- **构建引擎增强**
  - `build_pyw()` 方法添加输出目录验证（自动创建 + 写权限检查）
  - 使用 `CREATE_NO_WINDOW` 标志替代错误组合，提升 Windows 兼容性
  - 临时文件使用 `tempfile.mkdtemp()` 管理，避免污染用户工作区

### 🐛 问题修复

- **Issue #1: stdout 重定向逻辑修复**
  - 修复了 `StringIO` 对象没有 `buffer` 属性的问题
  - 改为使用清晰的 if/else 分支替代三元表达式

- **Issue #2: Windows 进程创建标志修复**
  - 移除了错误组合的 `CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`
  - 现在仅使用 `CREATE_NO_WINDOW` 隐藏控制台窗口

- **Issue #3: build_pyw 路径验证修复**
  - 添加了输出目录存在性检查
  - 添加了目录写权限验证
  - 自动创建不存在的输出目录

- **Issue #4: venv 路径替换逻辑改进**
  - 不再依赖字符串 `.replace('python.exe', 'pythonw.exe')`
  - 使用安全的 `os.path.join(os.path.dirname(venv_path), 'pythonw.exe')` 构建路径

---

## [0.1.0-alpha] - 2026-05-03

### 🎉 初始版本

- 项目结构初始化
- 核心模块：`CodeGenerator` 和 `BuildEngine`
- CustomTkinter GUI 界面
- Gooey 参数 JSON 摄入器
- PyInstaller EXE 打包功能
- 基础瘦壳代理架构
