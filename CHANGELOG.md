# Changelog

所有重要的项目版本更新将在此文件中记录。

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
