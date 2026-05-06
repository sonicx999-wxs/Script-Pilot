# ======================================================================
# 功能模块：代理代码生成器 (Agent Code Generator)
# ======================================================================
# 核心改动：重写了自举注入模块，引入了基于 tkinter.ttk 的多线程异步进度条界面。
#           新增：generate_lite_console_code() 函数，支持 default_args 参数预填。
# ======================================================================

import os
import sys

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
        venv_pythonw = ""
        if venv_path:
            venv_dir = os.path.dirname(venv_path)
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
            pip_exe = sys.executable
            if pip_exe.endswith('pythonw.exe'):
                pip_dir = os.path.dirname(pip_exe)
                pip_exe = os.path.join(pip_dir, 'python.exe')
            subprocess.check_call([pip_exe, "-m", "pip", "install", "gooey", "six"], creationflags=0x08000000)
            root.after(0, on_success)
        except Exception as e:
            root.after(0, on_fail, str(e))

    def on_success():
        root.destroy()
        subprocess.Popen([sys.executable, __file__])
        sys.exit(0)

    def on_fail(err_msg):
        root.withdraw()
        messagebox.showerror("安装失败", f"自动安装失败，请检查网络。\\n错误信息: {{err_msg}}")
        sys.exit(1)

    root = tk.Tk()
    root.title("环境初始化")

    window_width = 450
    window_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    root.geometry(f"{{window_width}}x{{window_height}}+{{x_cordinate}}+{{y_cordinate}}")

    root.resizable(False, False)
    root.attributes("-topmost", True)

    tk.Label(root, text="首次运行，正在下载并配置 UI 引擎...", font=("微软雅黑", 11)).pack(pady=(25, 10))

    progress = ttk.Progressbar(root, orient="horizontal", length=350, mode="indeterminate")
    progress.pack(pady=10)
    progress.start(15)

    tk.Label(root, text="这可能需要 10~30 秒，请耐心等待", font=("微软雅黑", 9), fg="gray").pack()

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

    clear_before_run=True,
    show_stop_warning=True,
    show_success_modal=False,
    show_failure_modal=True,
    navigation='sidebar',

    terminal_panel_color='#f8f9fa',
    terminal_font_color='#212529',
    terminal_font_family='Consolas',
    terminal_font_size=10
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


def generate_lite_console_code(metadata: dict, default_args: str = "") -> str:
    """
    生成极简交互控制台代码（基于原生 tkinter，零依赖）

    :param metadata: dict, 包含 title, venv_path, script_path
    :param default_args: str, 预填的命令行参数（空格分隔）
    :return: str, 完整的 Python 源码字符串
    """
    title = metadata.get('title', '极简控制台')
    venv_path = metadata.get('venv_path', '').strip().replace('\\', '\\\\')
    script_path = metadata.get('script_path', '').strip().replace('\\', '\\\\')

    venv_pythonw = ""
    if venv_path:
        venv_dir = os.path.dirname(venv_path)
        venv_pythonw = os.path.join(venv_dir, 'pythonw.exe')

    if venv_path:
        cmd_python = venv_path.replace('\\\\', '\\')
        cmd_script = script_path.replace('\\\\', '\\')
    else:
        cmd_python = sys.executable
        cmd_script = script_path.replace('\\\\', '\\')

    template = '''# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import threading
import queue
import ctypes
import traceback
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

TARGET_PYTHONW = r"{venv_pythonw}"
if TARGET_PYTHONW and os.path.exists(TARGET_PYTHONW):
    if os.path.normcase(sys.executable) != os.path.normcase(TARGET_PYTHONW):
        subprocess.Popen([TARGET_PYTHONW, __file__])
        sys.exit(0)

import tkinter as tk
from tkinter import scrolledtext

class LiteConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("{title}")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")

        self.process = None
        self.output_queue = queue.Queue()
        self.script_args = []

        self._build_ui()
        self.root.after(100, self._check_queue)
        self._show_args_dialog()

    def _build_ui(self):
        self.header_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.header_frame.pack(fill="x", padx=10, pady=5)

        self.header_label = tk.Label(
            self.header_frame,
            text="{title}",
            font=("微软雅黑", 12, "bold"),
            fg="#212529",
            bg="#f8f9fa"
        )
        self.header_label.pack(anchor="w")

        self.log_frame = tk.Frame(self.root, borderwidth=1, relief="solid", bg="#adb5bd")
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            bg="#f8f9fa",
            fg="#212529",
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            borderwidth=0
        )
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)

        self.input_frame = tk.Frame(self.root, borderwidth=1, relief="solid", bg="#adb5bd")
        self.input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.input_label = tk.Label(self.input_frame, text="> ", font=("Consolas", 10), bg="#f8f9fa")
        self.input_label.pack(side="left", padx=5, pady=5)

        self.input_entry = tk.Entry(
            self.input_frame,
            font=("Consolas", 10),
            width=80,
            bg="#f8f9fa",
            fg="#212529",
            insertbackground="#212529",
            relief="flat"
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=5)
        self.input_entry.bind("<Return>", self._send_input)
        self.input_entry.focus_set()

    def _show_args_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("参数配置")
        dialog.geometry("450x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#f8f9fa")

        window_width = 450
        window_height = 220
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        dialog.geometry(str(window_width) + "x" + str(window_height) + "+" + str(x_cordinate) + "+" + str(y_cordinate))

        tk.Label(dialog, text="请输入脚本的命令行参数（空格分隔）:", font=("微软雅黑", 11), fg="#212529", bg="#f8f9fa").pack(pady=(15, 5), padx=10, anchor="w")
        tk.Label(dialog, text="例如: --source /path/to/src --target /path/to/dst", font=("微软雅黑", 9), fg="gray", bg="#f8f9fa").pack(pady=(0, 10), padx=10, anchor="w")

        self.args_var = tk.StringVar(value="{default_args}")
        args_entry = tk.Entry(dialog, textvariable=self.args_var, width=60, font=("Consolas", 11), bg="white", fg="#212529", relief="solid", borderwidth=1)
        args_entry.pack(pady=(0, 15), padx=10, fill="x")
        args_entry.focus_set()

        button_frame = tk.Frame(dialog, bg="#f8f9fa")
        button_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(button_frame, text="直接运行（无参数）", font=("微软雅黑", 10), bg="#e9ecef", fg="#212529", relief="solid", borderwidth=1, padx=10, command=lambda: self._on_args_confirmed(dialog, "")).pack(side="left", padx=(0, 10))
        tk.Button(button_frame, text="确定", font=("微软雅黑", 10), bg="#495057", fg="white", relief="solid", borderwidth=1, padx=15, command=lambda: self._on_args_confirmed(dialog, self.args_var.get())).pack(side="right")

        dialog.bind("<Return>", lambda e: self._on_args_confirmed(dialog, self.args_var.get()))

    def _on_args_confirmed(self, dialog, args_str):
        dialog.destroy()
        if args_str.strip():
            self.script_args = args_str.split()
        else:
            self.script_args = []
        self._start_script()

    def _start_script(self):
        try:
            target_script = r"{cmd_script}"
            python_exe = r"{cmd_python}"

            self.log("[Lite-Terminal] 启动目标脚本...", "info")
            self.log("Python 解释器: " + python_exe, "info")
            self.log("目标脚本: " + target_script, "info")

            if not os.path.exists(target_script):
                error_msg = "[错误] 脚本文件不存在: " + target_script
                self.log(error_msg, "error")
                self._write_crash_log(error_msg)
                return

            cmd = [python_exe, target_script] + self.script_args
            self.log("执行命令: " + " ".join(cmd), "info")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            self.log("[进程已启动，PID: " + str(self.process.pid) + "]", "info")

            threading.Thread(target=self._read_output, daemon=True).start()

        except FileNotFoundError as e:
            error_msg = "[错误] 找不到 Python 解释器: " + str(e)
            self.log(error_msg, "error")
            self._write_crash_log(error_msg)
        except Exception as e:
            error_msg = "[错误] 启动失败: " + traceback.format_exc()
            self.log(error_msg, "error")
            self._write_crash_log(error_msg)

    def _read_output(self):
        if self.process:
            try:
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        self.output_queue.put(('output', line))
                self.process.wait()
                self.output_queue.put(('exit', self.process.returncode))
            except Exception as e:
                self.output_queue.put(('error', str(e)))

    def _check_queue(self):
        while not self.output_queue.empty():
            msg_type, data = self.output_queue.get()
            if msg_type == 'output':
                self.log(data, "output")
            elif msg_type == 'exit':
                self.log("\\n[进程结束] 退出码: " + str(data), "info")
                self.input_entry.config(state="disabled")
            elif msg_type == 'error':
                self.log("\\n[线程错误] " + data, "error")
        self.root.after(50, self._check_queue)

    def _send_input(self, event):
        if self.process and self.process.poll() is None:
            text = self.input_entry.get()
            if text.strip():
                self.log("> " + text + "\\n", "input")
                try:
                    self.process.stdin.write(text + "\\n")
                    self.process.stdin.flush()
                except Exception as e:
                    self.log("发送失败: " + str(e), "error")
                self.input_entry.delete(0, "end")

    def log(self, text, msg_type="output"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _write_crash_log(self, error_msg):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            crash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lite_console_crash_" + timestamp + ".log")
            with open(crash_path, "w", encoding="utf-8") as f:
                f.write("=== Lite-Terminal 崩溃日志 ===\\n")
                f.write("时间: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\\n")
                f.write(error_msg)
        except:
            pass

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = LiteConsole(root)
        root.mainloop()
    except Exception as e:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        crash_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lite_console_crash_" + timestamp + ".log")
        try:
            with open(crash_log_path, "w", encoding="utf-8") as f:
                f.write("=== Lite-Terminal 启动崩溃日志 ===\\n")
                f.write("时间: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\\n")
                f.write(traceback.format_exc())
        except:
            pass
'''
    return template.format(
        title=title,
        venv_pythonw=venv_pythonw,
        cmd_python=cmd_python,
        cmd_script=cmd_script,
        default_args=default_args
    )