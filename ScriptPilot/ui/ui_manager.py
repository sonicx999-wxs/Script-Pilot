# ui/ui_manager.py
import customtkinter as ctk
import json
import threading
import os
from tkinter import filedialog, messagebox

# 导入核心引擎
from core.code_generator import generate_proxy_code
from core.build_engine import BuildEngine
from __version__ import get_version_info

# 设置全局主题
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ScriptPilotUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(get_version_info())
        self.geometry("850x750")
        self.resizable(False, False)
        
        # 核心布局：分为左右两栏
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_panel()

    def _build_left_panel(self):
        """左侧面板：基础路径与元数据配置"""
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(frame, text="1. 核心路径配置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15), anchor="w", padx=10)
        
        # 目标脚本路径
        self.script_path_var = ctk.StringVar()
        self._add_path_row(frame, "目标 Python 脚本 (.py):", self.script_path_var, is_dir=False)
        
        # 独立 Venv 路径
        self.venv_path_var = ctk.StringVar()
        self._add_path_row(frame, "独立 Venv 解释器 (python.exe):", self.venv_path_var, is_dir=False)
        
        ctk.CTkLabel(frame, text="2. 启动器元数据", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15), anchor="w", padx=10)
        
        # 标题与描述
        self.title_var = ctk.StringVar(value="我的工具启动器")
        self._add_input_row(frame, "启动器名称 (EXE 名称):", self.title_var)
        
        self.desc_var = ctk.StringVar(value="由 Script-Pilot 自动生成")
        self._add_input_row(frame, "详细描述 (显示在界面上):", self.desc_var)
        
        # 输出目录
        self.output_dir_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        self._add_path_row(frame, "EXE 输出保存目录:", self.output_dir_var, is_dir=True)

    def _build_right_panel(self):
        """右侧面板：AI JSON 摄入器"""
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        ctk.CTkLabel(frame, text="3. AI 参数摄入器 (JSON Ingestor)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2f81f7").pack(pady=(10, 5), anchor="w", padx=10)
        ctk.CTkLabel(frame, text="请将 AI 提取的标准 JSON 数组直接粘贴至下方：", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10, pady=(0, 10))
        
        # JSON 文本框
        self.json_textbox = ctk.CTkTextbox(frame, height=450, font=ctk.CTkFont(family="Consolas", size=13))
        self.json_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 默认占位提示
        default_json = '[\n  {\n    "name": "--file",\n    "widget": "FileChooser",\n    "help": "请选择目标文件",\n    "required": true,\n    "default": ""\n  }\n]'
        self.json_textbox.insert("0.0", default_json)
        
        # 格式校验按钮
        self.btn_validate = ctk.CTkButton(frame, text="验证 JSON 格式", fg_color="#4B5563", hover_color="#374151", command=self._validate_json)
        self.btn_validate.pack(pady=10, padx=10, fill="x")

    def _build_bottom_panel(self):
        """底部面板：操作区"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(frame, text="就绪 (Ready)", font=ctk.CTkFont(size=14))
        self.status_label.pack(side="left", padx=10)
        
        self.btn_build = ctk.CTkButton(frame, text="⚡ 一键生成启动器 (Build EXE)", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#10b981", hover_color="#059669", command=self._start_build_thread)
        self.btn_build.pack(side="right", fill="x", expand=True, padx=(50, 0))

    # --- 辅助 UI 组件生成器 ---
    def _add_path_row(self, parent, label_text, string_var, is_dir=False):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", padx=10)
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))
        entry = ctk.CTkEntry(row, textvariable=string_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        btn = ctk.CTkButton(row, text="浏览", width=60, command=lambda: self._browse(string_var, is_dir))
        btn.pack(side="right")

    def _add_input_row(self, parent, label_text, string_var):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", padx=10)
        ctk.CTkEntry(parent, textvariable=string_var).pack(fill="x", padx=10, pady=(0, 10))

    def _browse(self, string_var, is_dir):
        if is_dir:
            path = filedialog.askdirectory()
        else:
            path = filedialog.askopenfilename()
        if path:
            string_var.set(path)

    # --- 核心业务逻辑 ---
    def _validate_json(self) -> list:
        """校验 JSON 格式并返回解析后的列表，失败返回 None"""
        raw_text = self.json_textbox.get("0.0", "end").strip()
        if not raw_text:
            return[]
        try:
            parsed = json.loads(raw_text)
            if not isinstance(parsed, list):
                raise ValueError("JSON 必须是一个数组 (List) 格式。")
            self.status_label.configure(text="✅ JSON 格式校验通过", text_color="#10b981")
            return parsed
        except Exception as e:
            messagebox.showerror("JSON 格式错误", f"解析失败，请检查 AI 输出的格式:\n{str(e)}")
            self.status_label.configure(text="❌ JSON 格式错误", text_color="#ef4444")
            return None

    def _start_build_thread(self):
        """主线程触发：收集数据并启动后台编译线程"""
        # 1. 基础校验
        if not self.script_path_var.get() or not self.venv_path_var.get():
            messagebox.showwarning("缺少路径", "请先填入目标脚本和 Venv 解释器的路径！")
            return
            
        params = self._validate_json()
        if params is None:
            return # JSON 错误，终止
            
        # 2. 锁定 UI
        self.btn_build.configure(state="disabled", text="⚙️ 正在编译打包中，请稍候...")
        self.status_label.configure(text="🚀 正在生成代理源码并调用 PyInstaller...", text_color="#f59e0b")
        
        # 3. 收集元数据
        metadata = {
            "title": self.title_var.get(),
            "description": self.desc_var.get(),
            "venv_path": self.venv_path_var.get(),
            "script_path": self.script_path_var.get()
        }
        output_dir = self.output_dir_var.get()
        exe_name = self.title_var.get()
        
        # 4. 启动后台线程
        threading.Thread(target=self._build_process, args=(metadata, params, output_dir, exe_name), daemon=True).start()

    def _build_process(self, metadata, params, output_dir, exe_name):
        """后台线程：执行耗时的编译操作"""
        try:
            # Step 1: 生成源码
            source_code = generate_proxy_code(metadata, params)
            
            # Step 2: 调用引擎编译
            engine = BuildEngine()
            success = engine.build_exe(source_code, output_dir, exe_name)
            
            # Step 3: 恢复 UI (必须通过 after 方法回传给主线程)
            if success:
                self.after(0, lambda: self._build_complete(True, f"✅ 编译成功！已保存至: {output_dir}"))
            else:
                self.after(0, lambda: self._build_complete(False, "❌ 编译失败，请查看控制台日志。"))
                
        except Exception as e:
            self.after(0, lambda: self._build_complete(False, f"❌ 发生严重错误: {str(e)}"))

    def _build_complete(self, success, msg):
        """主线程回调：恢复 UI 状态"""
        self.btn_build.configure(state="normal", text="⚡ 一键生成启动器 (Build EXE)")
        color = "#10b981" if success else "#ef4444"
        self.status_label.configure(text=msg, text_color=color)
        if success:
            messagebox.showinfo("大功告成", msg)
        else:
            messagebox.showerror("编译失败", msg)