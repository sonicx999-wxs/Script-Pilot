# ======================================================================
# 主入口文件 (Main Entry Point)
# ======================================================================

# main.py
import sys
import os

# 确保在打包或直接运行时，能正确找到 core 和 ui 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.ui_manager import ScriptPilotUI

def main():
    # 启动 GUI 主循环
    app = ScriptPilotUI()
    app.mainloop()

if __name__ == "__main__":
    # 隐藏 Windows 控制台的小技巧 (如果后续要把 Script-Pilot 自己也打包)
    # 但在开发阶段，我们保留控制台以查看 PyInstaller 的底层日志
    main()
