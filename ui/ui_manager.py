# ======================================================================
# 功能模块：UI 界面 (UI Manager)
# ======================================================================
# 核心改动：引入了 _load_config 和 _save_config 机制。每次启动自动读取，每次点击生成自动保存。
# ======================================================================

# ui/ui_manager.py
import customtkinter as ctk
import json
import threading
import os
import traceback
from tkinter import filedialog, messagebox

from core.code_generator import generate_proxy_code
from core.build_engine import BuildEngine
from __version__ import get_version_info

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "script_pilot_history.json"

class ScriptPilotUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(get_version_info())
        self.geometry("850x750")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # 初始化变量
        self.script_path_var = ctk.StringVar()
        self.venv_path_var = ctk.StringVar()
        self.title_var = ctk.StringVar(value="我的工具启动器")
        self.desc_var = ctk.StringVar(value="由 Script-Pilot 自动生成")
        self.output_dir_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.build_mode_var = ctk.StringVar(value="pyw")
        
        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_panel()
        
        #[架构师增强] 启动时自动加载历史配置
        self._load_config()

    def _build_left_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(frame, text="1. 核心路径配置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15), anchor="w", padx=10)
        self._add_path_row(frame, "目标 Python 脚本 (.py):", self.script_path_var, is_dir=False)
        self._add_path_row(frame, "独立 Venv 解释器 (留空则使用系统环境):", self.venv_path_var, is_dir=False)
        
        ctk.CTkLabel(frame, text="2. 启动器元数据", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15), anchor="w", padx=10)
        self._add_input_row(frame, "启动器名称:", self.title_var)
        self._add_input_row(frame, "详细描述 (显示在界面上):", self.desc_var)
        self._add_path_row(frame, "输出保存目录:", self.output_dir_var, is_dir=True)

    def _build_right_panel(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        ctk.CTkLabel(frame, text="3. AI 参数摄入器 (JSON Ingestor)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2f81f7").pack(pady=(10, 5), anchor="w", padx=10)
        ctk.CTkLabel(frame, text="请将 AI 提取的标准 JSON 数组直接粘贴至下方：", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10, pady=(0, 10))
        
        self.json_textbox = ctk.CTkTextbox(frame, height=450, font=ctk.CTkFont(family="Consolas", size=13))
        self.json_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.btn_validate = ctk.CTkButton(frame, text="验证 JSON 格式", fg_color="#4B5563", hover_color="#374151", command=self._validate_json)
        self.btn_validate.pack(pady=10, padx=10, fill="x")

    def _build_bottom_panel(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        
        mode_frame = ctk.CTkFrame(frame, fg_color="transparent")
        mode_frame.pack(side="left", padx=10)
        
        rb1 = ctk.CTkRadioButton(mode_frame, text="生成智能 .pyw 启动器 (推荐/极速/约5KB)", variable=self.build_mode_var, value="pyw")
        rb1.pack(anchor="w", pady=2)
        
        rb2 = ctk.CTkRadioButton(mode_frame, text="生成独立 .exe 启动器 (发给他人/约35MB)", variable=self.build_mode_var, value="exe")
        rb2.pack(anchor="w", pady=2)
        
        self.status_label = ctk.CTkLabel(frame, text="就绪 (Ready)", font=ctk.CTkFont(size=14))
        self.status_label.pack(side="left", padx=20)
        
        self.btn_build = ctk.CTkButton(frame, text="⚡ 立即生成启动器", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#10b981", hover_color="#059669", command=self._start_build_thread)
        self.btn_build.pack(side="right", fill="x", expand=True, padx=(20, 0))

    # --- 辅助 UI 组件 ---
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

    # --- 历史记录与配置管理 ---
    def _load_config(self):
        """加载历史配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.script_path_var.set(config.get("script_path", ""))
                self.venv_path_var.set(config.get("venv_path", ""))
                self.title_var.set(config.get("title", "我的工具启动器"))
                self.desc_var.set(config.get("desc", "由 Script-Pilot 自动生成"))
                self.output_dir_var.set(config.get("output_dir", os.path.join(os.path.expanduser("~"), "Desktop")))
                self.build_mode_var.set(config.get("build_mode", "pyw"))
                
                json_text = config.get("json_text", "")
                if json_text:
                    self.json_textbox.delete("0.0", "end")
                    self.json_textbox.insert("0.0", json_text)
            except Exception as e:
                print(f"读取历史配置失败: {e}")
        else:
            # 默认 JSON
            default_json = '[\n  {\n    "name": "--file",\n    "widget": "FileChooser",\n    "help": "请选择目标文件",\n    "required": true,\n    "default": ""\n  }\n]'
            self.json_textbox.insert("0.0", default_json)

    def _save_config(self):
        """保存当前配置到历史记录"""
        config = {
            "script_path": self.script_path_var.get(),
            "venv_path": self.venv_path_var.get(),
            "title": self.title_var.get(),
            "desc": self.desc_var.get(),
            "output_dir": self.output_dir_var.get(),
            "build_mode": self.build_mode_var.get(),
            "json_text": self.json_textbox.get("0.0", "end").strip()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存历史配置失败: {e}")

    # --- 核心业务逻辑 ---
    def _validate_json(self) -> list:
        raw_text = self.json_textbox.get("0.0", "end").strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
        if not raw_text:
            return[]
        try:
            parsed = json.loads(raw_text)
            if not isinstance(parsed, list):
                raise ValueError("JSON 必须是一个数组 (List) 格式。")
            self.status_label.configure(text="✅ JSON 格式校验通过", text_color="#10b981")
            return parsed
        except Exception as e:
            messagebox.showerror("JSON 格式错误", f"解析失败:\n{str(e)}")
            self.status_label.configure(text="❌ JSON 格式错误", text_color="#ef4444")
            return None

    def _start_build_thread(self):
        if not self.script_path_var.get():
            messagebox.showwarning("缺少路径", "请先填入目标脚本的路径！")
            return
            
        params = self._validate_json()
        if params is None:
            return
            
        #[架构师增强] 点击生成时自动保存当前配置
        self._save_config()
            
        mode = self.build_mode_var.get()
        
        self.btn_build.configure(state="disabled", text="⚙️ 正在生成中，请稍候...")
        self.status_label.configure(text="🚀 正在执行引擎任务...", text_color="#f59e0b")
        
        metadata = {
            "title": self.title_var.get(),
            "description": self.desc_var.get(),
            "venv_path": self.venv_path_var.get(),
            "script_path": self.script_path_var.get()
        }
        output_dir = self.output_dir_var.get()
        exe_name = self.title_var.get()
        
        threading.Thread(target=self._build_process, args=(metadata, params, output_dir, exe_name, mode), daemon=True).start()

    def _build_process(self, metadata, params, output_dir, exe_name, mode):
        try:
            source_code = generate_proxy_code(metadata, params, mode)
            engine = BuildEngine()
            
            if mode == 'pyw':
                success = engine.build_pyw(source_code, output_dir, exe_name)
                ext = ".pyw"
            else:
                success = engine.build_exe(source_code, output_dir, exe_name)
                ext = ".exe"
            
            if success:
                self.after(0, lambda: self._build_complete(True, f"✅ 成功！已保存: {exe_name}{ext}"))
            else:
                self.after(0, lambda: self._build_complete(False, "❌ 生成失败，请查看控制台日志。"))
                
        except Exception as e:
            traceback.print_exc()
            self.after(0, lambda: self._build_complete(False, f"❌ 发生严重错误: {repr(e)}"))

    def _build_complete(self, success, msg):
        self.btn_build.configure(state="normal", text="⚡ 立即生成启动器")
        color = "#10b981" if success else "#ef4444"
        self.status_label.configure(text=msg, text_color=color)
        if success:
            messagebox.showinfo("大功告成", msg)
        else:
            messagebox.showerror("生成失败", msg)