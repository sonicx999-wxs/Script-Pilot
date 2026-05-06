# ======================================================================
# 功能模块：UI 界面 (UI Manager) - V3.5
# ======================================================================
# 核心改动：
# - 详细日志控制开关（Verbose Mode）
# - 实时编译日志管道（log_callback）
# - 进度条平滑呼吸动画
# - verbose 状态持久化到历史 JSON
# ======================================================================

import customtkinter as ctk
import json
import threading
import os
import traceback
from tkinter import filedialog, messagebox

from core.code_generator import generate_proxy_code, generate_lite_console_code
from core.build_engine import BuildEngine
from core.analyzer import analyze_script, extract_arg_names, get_script_hash
from __version__ import get_version_info

try:
    from pygments import lex
    from pygments.lexers import PythonLexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
    
    TOKEN_COLORS = {
        Token.Keyword: '#569CD6',
        Token.Keyword.Constant: '#569CD6',
        Token.Keyword.Declaration: '#569CD6',
        Token.Keyword.Namespace: '#569CD6',
        Token.Name.Builtin: '#4EC9B0',
        Token.Name.Function: '#DCDCAA',
        Token.Name.Class: '#4EC9B0',
        Token.Name.Decorator: '#4EC9B0',
        Token.String: '#CE9178',
        Token.Number: '#B5CEA8',
        Token.Comment: '#6A9955',
        Token.Operator: '#D4D4D4',
        Token.Punctuation: '#D4D4D4',
        Token.Text: '#D4D4D4',
    }
except ImportError:
    PYGMENTS_AVAILABLE = False
    TOKEN_COLORS = {}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "script_pilot_history.json"

class ScriptPilotUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(get_version_info())
        self.geometry("950x750")
        
        self.minsize(800, 600)
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.script_path_var = ctk.StringVar()
        self.venv_path_var = ctk.StringVar()
        self.title_var = ctk.StringVar(value="我的工具启动器")
        self.desc_var = ctk.StringVar(value="由 Script-Pilot 自动生成")
        self.output_dir_var = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.build_mode_var = ctk.StringVar(value="pyw")
        self.verbose_var = ctk.BooleanVar(value=False)
        
        self.temp_json_buffer = ""
        self.log_textbox = None
        self.progress_bar = None
        self._verbose_line_count = 0

        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_panel()

        self._load_config()

    def _build_left_panel(self):
        frame = ctk.CTkFrame(self, width=400)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_propagate(False)

        ctk.CTkLabel(frame, text="1. 核心路径配置", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 15), anchor="w", padx=10)
        self._add_path_row(frame, "目标 Python 脚本 (.py):", self.script_path_var, is_dir=False)
        self._add_path_row(frame, "独立 Venv 解释器 (留空则使用系统环境):", self.venv_path_var, is_dir=False)

        ctk.CTkLabel(frame, text="2. 启动器元数据", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15), anchor="w", padx=10)
        self._add_input_row(frame, "启动器名称:", self.title_var)
        self._add_input_row(frame, "详细描述 (显示在界面上):", self.desc_var)
        self._add_path_row(frame, "输出保存目录:", self.output_dir_var, is_dir=True)

    def _build_right_panel(self):
        frame = ctk.CTkFrame(self, width=480)
        frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        frame.grid_propagate(False)

        ctk.CTkLabel(frame, text="3. 参数与预览", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2f81f7").pack(pady=(10, 5), anchor="w", padx=10)

        self.tabview = ctk.CTkTabview(frame, width=480)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_json = self.tabview.add("参数配置 (JSON)")
        self.tab_source = self.tabview.add("源码预览 (Source)")
        self.tab_log = self.tabview.add("运行日志 (Log)")

        self._build_json_tab()
        self._build_source_tab()
        self._build_log_tab()

    def _build_json_tab(self):
        container = ctk.CTkFrame(self.tab_json, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(container, text="请将 AI 提取的标准 JSON 数组直接粘贴至下方：", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.json_textbox = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=12))
        self.json_textbox.grid(row=1, column=0, sticky="nsew", pady=(0, 5))

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=0)
        btn_frame.grid_columnconfigure(0, weight=1, uniform="btn_group")
        btn_frame.grid_columnconfigure(1, weight=1, uniform="btn_group")
        btn_frame.grid_columnconfigure(2, weight=1, uniform="btn_group")

        self.btn_undo = ctk.CTkButton(btn_frame, text="撤销 (Undo)", fg_color="#6B7280", hover_color="#4B5563", command=self._undo_clear)
        self.btn_undo.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.btn_clear = ctk.CTkButton(btn_frame, text="清空 (Clear)", fg_color="#DC2626", hover_color="#B91C1C", command=self._manual_clear)
        self.btn_clear.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_validate = ctk.CTkButton(btn_frame, text="验证 JSON", fg_color="#4B5563", hover_color="#374151", command=self._validate_json)
        self.btn_validate.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def _build_source_tab(self):
        container = ctk.CTkFrame(self.tab_source, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(container, text="脚本源码预览（自动更新）", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.source_textbox = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=11), state="disabled")
        self.source_textbox.grid(row=1, column=0, sticky="nsew")

        if not PYGMENTS_AVAILABLE:
            ctk.CTkLabel(container, text="提示: pip install pygments 可启用语法高亮", font=ctk.CTkFont(size=10), text_color="gray").grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _build_log_tab(self):
        container = ctk.CTkFrame(self.tab_log, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="运行日志（自动记录）", font=ctk.CTkFont(size=12), text_color="gray").pack(side="left")

        self.verbose_checkbox = ctk.CTkCheckBox(header_frame, text="显示详细编译记录 (Verbose Mode)",
                                                variable=self.verbose_var, onvalue=True, offvalue=False,
                                                font=ctk.CTkFont(size=11), border_width=2,
                                                checkbox_width=18, checkbox_height=18,
                                                fg_color="#2f81f7", hover_color="#1a6bd6")
        self.verbose_checkbox.pack(side="right", padx=(0, 5))

        self.log_textbox = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=11), state="disabled")
        self.log_textbox.grid(row=1, column=0, sticky="nsew")

        self._log_message("欢迎使用 Script-Pilot V3.5", "info")
        self._log_message("选择脚本后将自动分析并显示推荐模式", "info")
        self._log_message("勾选 Verbose 开关可查看详细编译日志", "info")
        self._log_message("==================================", "info")

    def _build_bottom_panel(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 8), sticky="ew")

        mode_frame = ctk.CTkFrame(frame, fg_color="transparent")
        mode_frame.pack(side="left", padx=10)
        mode_frame.grid_columnconfigure(0, weight=0)
        mode_frame.grid_columnconfigure(1, weight=1)

        badge_style = {
            "font": ctk.CTkFont(size=11, weight="bold"),
            "corner_radius": 6,
            "text_color": "white",
            "padx": 8,
            "pady": 2
        }
        
        # V3.4: UI 重排 - Row 0: lite_console, Row 1: pyw, Row 2: exe
        self.badge_lite = ctk.CTkLabel(mode_frame, text="", **badge_style)
        self.badge_lite.grid(row=0, column=0, padx=(0, 10), pady=1)
        
        self.badge_pyw = ctk.CTkLabel(mode_frame, text="", **badge_style)
        self.badge_pyw.grid(row=1, column=0, padx=(0, 10), pady=1)
        
        self.badge_exe = ctk.CTkLabel(mode_frame, text="", **badge_style)
        self.badge_exe.grid(row=2, column=0, padx=(0, 10), pady=1)

        rb1 = ctk.CTkRadioButton(mode_frame, text="生成极简交互控制台 (零依赖/交互版/约12KB)", variable=self.build_mode_var, value="lite_console", command=self._on_mode_changed)
        rb1.grid(row=0, column=1, sticky="w", pady=1)

        rb2 = ctk.CTkRadioButton(mode_frame, text="生成智能 .pyw 启动器 (推荐/极速/约5KB)", variable=self.build_mode_var, value="pyw", command=self._on_mode_changed)
        rb2.grid(row=1, column=1, sticky="w", pady=1)

        rb3 = ctk.CTkRadioButton(mode_frame, text="生成独立 .exe 启动器 (发给他人/约35MB)", variable=self.build_mode_var, value="exe", command=self._on_mode_changed)
        rb3.grid(row=2, column=1, sticky="w", pady=1)

        btn_area = ctk.CTkFrame(frame, fg_color="transparent", width=360)
        btn_area.pack(side="right", padx=(20, 20), fill="both")
        btn_area.grid_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(btn_area, height=6, progress_color="#10b981")
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        self.status_label = ctk.CTkLabel(btn_area, text="就绪 (Ready)", font=ctk.CTkFont(size=14))
        self.status_label.pack(fill="x", pady=(0, 5))

        self.btn_build = ctk.CTkButton(btn_area, text="⚡ 立即生成启动器", font=ctk.CTkFont(size=16, weight="bold"), 
                                       height=40, width=320,
                                       fg_color="#10b981", hover_color="#059669", 
                                       command=self._start_build_thread)
        self.btn_build.pack(fill="x")

    def _on_mode_changed(self):
        pass

    def _clear_all_badges(self):
        """V3.4: 清空所有徽章"""
        self.badge_pyw.configure(text="", fg_color="transparent")
        self.badge_exe.configure(text="", fg_color="transparent")
        self.badge_lite.configure(text="", fg_color="transparent")

    def _show_only_recommendation(self, recommended_mode):
        """V3.4: 徽章显隐逻辑 - 仅对 pyw 和 lite_console 显示推荐徽章"""
        self._clear_all_badges()
        
        if recommended_mode == "lite_console":
            self.badge_lite.configure(text="推荐", fg_color="#10b981")
        elif recommended_mode == "pyw" or recommended_mode == "gooey":
            self.badge_pyw.configure(text="推荐", fg_color="#10b981")
            if recommended_mode == "gooey":
                self.build_mode_var.set("pyw")
        elif recommended_mode == "exe":
            pass

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
            path = filedialog.askopenfilename(filetypes=[("Python Scripts", "*.py")])
        if path:
            old_path = string_var.get()
            string_var.set(path)

            if string_var == self.script_path_var:
                script_name = os.path.basename(path)
                script_name_no_ext = os.path.splitext(script_name)[0]
                launcher_name = f"{script_name_no_ext}脚本的启动器"
                self.title_var.set(launcher_name)

                new_hash = get_script_hash(path)
                self._load_history_by_hash(new_hash)

                if old_path and old_path != path:
                    current_json = self.json_textbox.get("0.0", "end").strip()
                    if current_json and current_json != self._get_default_json():
                        self.temp_json_buffer = current_json

                threading.Thread(target=self._analyze_and_update, args=(path,), daemon=True).start()

    def _load_history_by_hash(self, script_hash):
        if not script_hash:
            return

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                scripts = config.get("scripts", {})
                if script_hash in scripts:
                    saved_item = scripts[script_hash]
                    saved_json = saved_item.get("json", "")
                    saved_title = saved_item.get("title", "")
                    
                    if saved_json:
                        self.json_textbox.delete("0.0", "end")
                        self.json_textbox.insert("0.0", saved_json)
                    
                    if saved_title:
                        self.title_var.set(saved_title)
                    
                    self._log_message(f"检测到历史配置，已自动载入", "success")
            except Exception as e:
                print(f"加载历史配置失败: {e}")

    def _save_history_by_hash(self, script_hash):
        if not script_hash:
            return

        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception:
                pass

        scripts = config.get("scripts", {})
        scripts[script_hash] = {
            "json": self.json_textbox.get("0.0", "end").strip(),
            "title": self.title_var.get(),
            "last_used": os.path.basename(self.script_path_var.get())
        }
        config["scripts"] = scripts
        config["last_path"] = self.script_path_var.get()

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存历史配置失败: {e}")

    def _undo_clear(self):
        if self.temp_json_buffer:
            self.json_textbox.delete("0.0", "end")
            self.json_textbox.insert("0.0", self.temp_json_buffer)
            self._log_message("已恢复之前的 JSON 配置", "success")
        else:
            messagebox.showinfo("提示", "没有可恢复的内容")

    def _manual_clear(self):
        current_content = self.json_textbox.get("0.0", "end").strip()
        if current_content:
            self.temp_json_buffer = current_content
            self.json_textbox.delete("0.0", "end")
            self._log_message("已手动清空 JSON 配置", "warning")
        else:
            messagebox.showinfo("提示", "JSON 框已经是空的")

    def _get_default_json(self):
        return '[\n  {\n    "name": "--file",\n    "widget": "FileChooser",\n    "help": "请选择目标文件",\n    "required": true,\n    "default": ""\n  }\n]'

    def _analyze_and_update(self, script_path):
        try:
            result = analyze_script(script_path)
            self.after(0, lambda: self._update_ui_after_analysis(result, script_path))
        except Exception as e:
            print(f"脚本分析失败: {e}")

    def _update_ui_after_analysis(self, result, script_path):
        recommended = result['recommended_mode']
        confidence = result['confidence']
        features = result['detected_features']

        if confidence > 0.6:
            self._show_only_recommendation(recommended)
            actual_mode = "pyw" if recommended in ("gooey", "pyw") else recommended
            self.build_mode_var.set(actual_mode)
        else:
            self._clear_all_badges()

        self._log_message(f"脚本分析完成: {os.path.basename(script_path)}", "info")
        self._log_message(f"检测特性: {', '.join(features) if features else '无'}", "info")
        self._log_message(f"推荐模式: {recommended} (置信度: {confidence:.0%})", "success")

        self._update_source_preview(script_path)

    def _update_source_preview(self, script_path):
        if not os.path.exists(script_path):
            return

        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)

            self.source_textbox.configure(state="normal")
            
            if PYGMENTS_AVAILABLE:
                self._apply_pygments_highlighting(self.source_textbox, content)
            else:
                self.source_textbox.delete("1.0", "end")
                self.source_textbox.insert("1.0", content)

            self.source_textbox.configure(state="disabled")
            self._log_message("源码预览已更新", "info")
        except Exception as e:
            self._log_message(f"源码预览更新失败: {str(e)}", "error")

    def _apply_pygments_highlighting(self, text_widget, code):
        lexer = PythonLexer()
        text_widget.delete("1.0", "end")
        
        for tag in text_widget.tag_names():
            text_widget.tag_delete(tag)

        for token_type, token_text in lex(code, lexer):
            color = TOKEN_COLORS.get(token_type)
            if color is None:
                color = TOKEN_COLORS.get(type(token_type))
            if color is None:
                color = "#D4D4D4"

            tag_name = f"tag_{id(token_type)}_{hash(token_text) % 10000}"
            text_widget.tag_config(tag_name, foreground=color)
            text_widget.insert("end", token_text, tag_name)

    def _log_message(self, message, level="info"):
        if not self.log_textbox:
            return

        prefixes = {"info": "[INFO] ", "success": "[OK] ", "warning": "[WARN] ", "error": "[ERR] "}
        colors = {"info": "#9CA3AF", "success": "#10b981", "warning": "#F59E0B", "error": "#EF4444"}

        self.log_textbox.configure(state="normal")
        
        prefix_tag = f"prefix_{level}"
        self.log_textbox.tag_config(prefix_tag, foreground=colors.get(level, "#9CA3AF"))
        self.log_textbox.insert("end", prefixes.get(level, "[INFO] "), prefix_tag)
        
        msg_tag = f"msg_{level}"
        self.log_textbox.insert("end", message + "\n", msg_tag)
        
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _log_verbose(self, message):
        """V3.5: 输出详细日志（浅灰色 #6B7280）"""
        if not self.log_textbox:
            return

        self.log_textbox.configure(state="normal")
        verbose_tag = "verbose_line"
        self.log_textbox.tag_config(verbose_tag, foreground="#6B7280")
        self.log_textbox.insert("end", "  " + message + "\n", verbose_tag)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _load_config(self):
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
                self.verbose_var.set(config.get("verbose", False))

                json_text = config.get("json_text", "")
                if json_text:
                    self.json_textbox.delete("0.0", "end")
                    self.json_textbox.insert("0.0", json_text)

                if self.script_path_var.get():
                    self._update_source_preview(self.script_path_var.get())
            except Exception as e:
                print(f"读取历史配置失败: {e}")
        else:
            default_json = self._get_default_json()
            self.json_textbox.insert("0.0", default_json)

    def _save_config(self):
        script_hash = get_script_hash(self.script_path_var.get())
        self._save_history_by_hash(script_hash)

        config = {
            "script_path": self.script_path_var.get(),
            "venv_path": self.venv_path_var.get(),
            "title": self.title_var.get(),
            "desc": self.desc_var.get(),
            "output_dir": self.output_dir_var.get(),
            "build_mode": self.build_mode_var.get(),
            "verbose": self.verbose_var.get(),
            "json_text": self.json_textbox.get("0.0", "end").strip()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存历史配置失败: {e}")

    def _validate_json(self) -> list:
        raw_text = self.json_textbox.get("0.0", "end").strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
        if not raw_text:
            return []
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

        mode = self.build_mode_var.get()

        if mode != 'lite_console':
            params = self._validate_json()
            if params is None:
                return

        self._save_config()

        self.btn_build.configure(state="disabled", text="⚙️ 正在生成中...")
        self.status_label.configure(text="🚀 正在执行引擎任务...", text_color="#f59e0b")
        self._log_message("开始生成启动器...", "info")
        
        self.tabview.set("运行日志 (Log)")

        if mode == 'exe':
            self.progress_bar.set(0)
            self.progress_bar.pack(fill="x", pady=(0, 5), before=self.status_label)
            self.progress_bar.start()

        metadata = {
            "title": self.title_var.get(),
            "description": self.desc_var.get(),
            "venv_path": self.venv_path_var.get(),
            "script_path": self.script_path_var.get()
        }
        output_dir = self.output_dir_var.get()
        exe_name = self.title_var.get()

        threading.Thread(target=self._build_process, args=(metadata, output_dir, exe_name, mode), daemon=True).start()

    def _build_process(self, metadata, output_dir, exe_name, mode):
        try:
            engine = BuildEngine()
            default_args = ""
            self._verbose_line_count = 0

            self.after(0, lambda: self._log_message("正在扫描脚本依赖...", "info"))
            
            if mode == 'lite_console':
                self.after(0, lambda: self._log_message("正在提取命令行参数...", "info"))
                arg_names = extract_arg_names(self.script_path_var.get())
                if arg_names:
                    default_args = " ".join(arg_names)
                self.after(0, lambda: self._log_message("正在生成 Lite-Terminal 源码...", "info"))
                source_code = generate_lite_console_code(metadata, default_args=default_args)
                success = engine.build_pyw(source_code, output_dir, exe_name)
                ext = ".pyw"
            elif mode == 'pyw':
                self.after(0, lambda: self._log_message("正在生成 .pyw 代理源码...", "info"))
                params = self._validate_json() or []
                source_code = generate_proxy_code(metadata, params, mode)
                success = engine.build_pyw(source_code, output_dir, exe_name)
                ext = ".pyw"
            else:
                self.after(0, lambda: self._log_message("正在初始化 PyInstaller 环境...", "info"))
                params = self._validate_json() or []
                source_code = generate_proxy_code(metadata, params, mode)
                self.after(0, lambda: self._log_message("正在编译 exe 文件（这可能需要几分钟）...", "info"))
                
                def _exe_log_callback(message, level):
                    if level == "verbose":
                        if self.verbose_var.get():
                            self.after(0, lambda msg=message: self._log_verbose(msg))
                        self._verbose_line_count += 1
                        if self._verbose_line_count % 5 == 0:
                            self.after(0, lambda: self.progress_bar.step())
                    elif level == "error":
                        self.after(0, lambda msg=message: self._log_message(msg, "error"))
                    else:
                        self.after(0, lambda msg=message, lvl=level: self._log_message(msg, lvl))
                
                success = engine.build_exe(source_code, output_dir, exe_name, log_callback=_exe_log_callback)
                ext = ".exe"

            if success:
                self.after(0, lambda: self._build_complete(True, f"✅ 成功！已保存: {exe_name}{ext}"))
            else:
                self.after(0, lambda: self._build_complete(False, "❌ 生成失败，请查看控制台日志。"))

        except Exception as e:
            traceback.print_exc()
            error_msg = f"❌ 发生严重错误: {repr(e)}"
            self.after(0, lambda msg=error_msg: self._build_complete(False, msg))

    def _build_complete(self, success, msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        self.btn_build.configure(state="normal", text="⚡ 立即生成启动器")
        color = "#10b981" if success else "#ef4444"
        self.status_label.configure(text=msg, text_color=color)
        
        if success:
            self._log_message(msg, "success")
            messagebox.showinfo("大功告成", msg)
        else:
            self._log_message(msg, "error")
            messagebox.showerror("生成失败", msg)