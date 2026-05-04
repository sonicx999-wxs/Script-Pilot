# ======================================================================
# 功能模块：代理代码生成器 (Agent Code Generator)
# ======================================================================
# 核心改动：重写了自举注入模块，引入了基于 tkinter.ttk 的多线程异步进度条界面。
# ======================================================================

# core/code_generator.py
import os

def generate_proxy_code(metadata: dict, params: list, mode: str = 'pyw') -> str:
    title = metadata.get('title', '未命名启动器')
    desc = metadata.get('description', '由 Script-Pilot 自动生成')
    venv_path = metadata.get('venv_path', '').strip().replace('\\', '\\\\')
    script_path = metadata.get('script_path', '').strip().replace('\\', '\\\\')

    if venv_path:
        cmd_init = f'    cmd =["{venv_path}", "{script_path}"]'
    else:
        cmd_init = f'    cmd =["python", "{script_path}"]'

    arg_lines = ""
    cmd_assembly_lines = ""
    for p in params:
        flag_name = p.get('name', '').strip()
        widget = p.get('widget', 'TextField')
        help_text = p.get('help', '')
        required = p.get('required', False)
        default = p.get('default', '')
        is_positional = not flag_name.startswith('-')
        dest_name = flag_name.lstrip('-').replace('-', '_')
        
        if is_positional:
            nargs_str = "" if required else ", nargs='?'"
            def_str = f", default='{default}'" if default else ""
            arg_lines += f"    parser.add_argument('{flag_name}', help='{help_text}'{nargs_str}{def_str}, widget='{widget}')\n"
            cmd_assembly_lines += f"    val = getattr(args, '{dest_name}', None)\n"
            cmd_assembly_lines += f"    if val is not None and str(val).strip() != '': cmd.append(str(val))\n"
        else:
            req_str = "True" if required else "False"
            def_str = f", default='{default}'" if default else ""
            arg_lines += f"    parser.add_argument('{flag_name}', help='{help_text}', required={req_str}{def_str}, widget='{widget}')\n"
            cmd_assembly_lines += f"    val = getattr(args, '{dest_name}', None)\n"
            cmd_assembly_lines += f"    if val is not None and str(val).strip() != '': cmd.extend(['{flag_name}', str(val)])\n"

    bootstrapping_code = ""
    if mode == 'pyw':
        # 使用更安全的路径构建方式，不依赖字符串替换
        venv_pythonw = ""
        if venv_path:
            # 获取 venv 解释器所在目录
            venv_dir = os.path.dirname(venv_path)
            # 在同一目录下寻找 pythonw.exe
            venv_pythonw = os.path.join(venv_dir, 'pythonw.exe')
        
        bootstrapping_code = f'''
# ==========================================
# 阶段一：环境接力 (Venv Handoff)
# ==========================================
TARGET_PYTHONW = r"{venv_pythonw}"
if TARGET_PYTHONW and os.path.exists(TARGET_PYTHONW):
    if os.path.normcase(sys.executable) != os.path.normcase(TARGET_PYTHONW):
        subprocess.Popen([TARGET_PYTHONW, __file__])
        sys.exit(0)

# ==========================================
# 阶段二：原生可视化自举注入 (Visual Bootstrapping)
# ==========================================
try:
    from gooey import Gooey, GooeyParser
    import six
except ImportError:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading

    def install_task():
        try:
            # 同样使用安全的路径构建方式
            pip_exe = sys.executable
            if pip_exe.endswith('pythonw.exe'):
                pip_dir = os.path.dirname(pip_exe)
                pip_exe = os.path.join(pip_dir, 'python.exe')
            subprocess.check_call([pip_exe, "-m", "pip", "install", "gooey", "six"], creationflags=0x08000000)
            # 安装成功，通知主线程关闭进度条并重启
            root.after(0, on_success)
        except Exception as e:
            # 安装失败，通知主线程弹窗报错
            root.after(0, on_fail, str(e))

    def on_success():
        root.destroy()
        subprocess.Popen([sys.executable, __file__])
        sys.exit(0)

    def on_fail(err_msg):
        root.withdraw()
        messagebox.showerror("安装失败", f"自动安装失败，请检查网络。\\n错误信息: {{err_msg}}")
        sys.exit(1)

    # 绘制原生加载窗口
    root = tk.Tk()
    root.title("环境初始化")
    
    # 居中显示窗口
    window_width = 450
    window_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    root.geometry(f"{{window_width}}x{{window_height}}+{{x_cordinate}}+{{y_cordinate}}")
    
    root.resizable(False, False)
    root.attributes("-topmost", True)  # 保持窗口在最前，防止被其他软件遮挡

    tk.Label(root, text="首次运行，正在下载并配置 UI 引擎...", font=("微软雅黑", 11)).pack(pady=(25, 10))
    
    # 动态进度条
    progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(15)  # 启动进度条动画
    
    tk.Label(root, text="这可能需要 10~30 秒，请耐心等待", font=("微软雅黑", 9), fg="gray").pack()

    # 启动后台安装线程，防止界面卡死
    threading.Thread(target=install_task, daemon=True).start()
    
    root.mainloop()
'''
    else:
        bootstrapping_code = "from gooey import Gooey, GooeyParser"

    template = f'''# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import io
import traceback

{bootstrapping_code}

# ==========================================
# 阶段三：物理设备挂载 (IO 修复)
# ==========================================
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
else:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')
else:
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        pass

@Gooey(
    program_name="{title}", 
    program_description="{desc}", 
    language='chinese',
    default_size=(720, 600),

    # === [高级 UI 定制区] ===
    clear_before_run=True,      # 运行前清空旧日志
    show_stop_warning=True,     # 点击停止按钮时弹出确认框
    show_success_modal=False,   # 运行成功后是否弹出提示框（设为True则多点一次确认）
    show_failure_modal=True,    # 运行失败后弹出提示框
    navigation='sidebar',       # 侧边栏模式（如果参数多，这个很酷）
    # show_restart_button=True, # 是否显示“再次运行”按钮
    # return_to_config=False,   # 运行结束后是否自动返回配置界面
    
    # 终端外观定制
    terminal_panel_color='#f8f9fa',   # 背景色
    terminal_font_color='#212529',    # 字体颜色
    terminal_font_family='Consolas',  # 字体类型
    terminal_font_size=10             # 字体大小
)
def main():
    parser = GooeyParser(description="请在下方填写运行参数：")
{arg_lines}
    args = parser.parse_args()

{cmd_init}
{cmd_assembly_lines}

    print("[*] 启动器准备就绪，正在调用业务脚本...", flush=True)
    
    try:
        current_env = os.environ.copy()
        current_env["PYTHONIOENCODING"] = "utf-8"
        current_env["PYTHONUTF8"] = "1"

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            stdin=subprocess.DEVNULL,
            env=current_env,
            text=True, 
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            creationflags=creationflags
        )
        
        for line in process.stdout:
            print(line, end='', flush=True)
            
        process.wait()
        sys.exit(process.returncode)
            
    except Exception as e:
        print(f"\\n[!] 启动器运行异常: {{str(e)}}", flush=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        crash_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt")
        with open(crash_log_path, "w", encoding="utf-8") as f:
            f.write("=== 启动器致命崩溃日志 ===\\n")
            f.write(traceback.format_exc())
'''
    return template