# Product Requirements Document (产品需求文档) - Script-Pilot

## 1. 项目代号与定位
* **项目名称:** Script-Pilot (暂定) / Py-Thin-Launcher
* **一句话定位:** 专为 AI 编程时代设计的“零代码 Python 瘦壳启动器生成引擎”。
* **核心理念:** 停止打包 100MB 的臃肿 EXE，将任意 Python 脚本瞬间转化为 2MB 的轻量级、带隔离环境的现代 GUI 启动器。除了解决“胖客户端”的痛点，Script-Pilot 引入了独创的 **“AI 提示词驱动流 (Prompt-Driven Workflow)”**：
* **标准传参契约 (The Parameter Contract):** 强制规定底层脚本必须使用 `argparse` 接收参数，并定义了一套标准的 JSON 参数描述格式。
* **快捷录入剪贴板 (JSON Paste Window):** APP 界面新增一个“参数批量粘贴窗口”。用户无需手动逐个添加控件，只需将 AI 提取的标准 JSON 格式直接粘贴进去，瞬间生成完整 UI 表单。

## 2. 初始点子与需求起源
在 AI 辅助编程普及的今天，编写底层 Python 逻辑变得极其简单，但**“脚本的本地化部署与交互”**却成为了新的瓶颈。传统的 C/S 架构 (Client/Server，客户端/服务端) 过于笨重，而传统的全量打包工具又导致磁盘浪费和启动缓慢。用户需要一种像“快捷方式”一样轻量，但具备现代 GUI 表单传参能力的“代理启动器”。

## 3. 市场调研与竞品分析 (Blue Ocean Strategy)
目前开源市场处于**生态位空白**：
* **重型打包派 (如 auto-py-to-exe):** 产出 Fat Client (胖客户端)，体积大(>50MB)，启动慢，每次修改底层脚本需重新耗时编译。
* **重型 UI 派 (如 Tkinter-Designer):** 产出复杂的 Event Loop (事件循环) 代码，非专业程序员极难维护，且违背了 AI 擅长写底层逻辑的优势。
* **Script-Pilot 的降维打击:** 采用 Thin Shell (瘦壳) 架构，彻底解耦“前端 UI”与“后端逻辑”。

## 4. 痛点击穿 (Pain Points Solved)
1. **The AI-GUI Dilemma (AI 界面困境):** 解决小白让 AI 写 GUI 代码极易崩溃的痛点。现在只需让 AI 写纯逻辑脚本，UI 由本工具一键生成。
2. **Fat-Client Bloat (胖客户端臃肿):** 解决本地脚本管理中，大量打包 EXE 导致的磁盘爆炸和启动迟滞。
3. **Terminal Phobia (终端恐惧症):** 彻底消灭黑框框，用现代表单替代命令行传参。
4. **Dependency Hell (依赖地狱):** 强制绑定独立 Virtual Environment (虚拟环境)，从物理层面根除包冲突。
5. **GUI 配置繁琐 (Tedious GUI Configuration):** 
即使是点选式生成工具，当脚本有 10 个参数时，手动配置依旧繁琐。
**解法:** 赋予用户一套标准 Prompt。让 AI 分析脚本并直接吐出 JSON 配置，用户只需 `Ctrl+C` 和 `Ctrl+V`，实现“秒级 UI 映射”。

## 5. 预计前景
该工具极具潜力成为 GitHub 上的爆款开源项目，成为数据分析师、运维工程师以及所有使用 IDE 辅助编程的 Python 初学者的“标配装机工具”。