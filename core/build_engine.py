# ======================================================================
# 功能模块：构建引擎 (Build Engine)
# ======================================================================
# V3.5: 添加 log_callback 实时日志管道，支持编译日志实时回传
# ======================================================================

import os
import sys
import subprocess
import tempfile
import shutil
import re
import select

class BuildEngine:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="script_pilot_")
        self.source_file = os.path.join(self.temp_dir, "launcher_proxy.py")

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名中的非法字符"""
        name = re.sub(r'[<>:"/\\|?*!@#$%^&*]', '_', name)
        name = name.strip()
        if not name:
            name = "launcher"
        return name

    def build_pyw(self, source_code: str, output_dir: str, exe_name: str) -> bool:
        """生成极轻量级的 .pyw 智能启动器 (瞬间完成)"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            if not os.access(output_dir, os.W_OK):
                print(f"[-] 无法写入目录: {output_dir}")
                return False
            
            exe_name_clean = self._sanitize_filename(exe_name)
            pyw_path = os.path.join(output_dir, f"{exe_name_clean}.pyw")
            with open(pyw_path, 'w', encoding='utf-8') as f:
                f.write(source_code)
            print(f"[+] 智能启动器生成成功！路径: {pyw_path}")
            return True
        except Exception as e:
            print(f"[-] 生成 .pyw 失败: {repr(e)}")
            return False

    def build_exe(self, source_code: str, output_dir: str, exe_name: str, icon_path: str = None, log_callback=None) -> bool:
        """生成独立 EXE (PyInstaller) - V3.5: 支持 log_callback 实时回传"""
        exe_name_clean = self._sanitize_filename(exe_name)
        
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--console",
            "--noconfirm",
            "--clean",
            "--hidden-import", "six",
            "--name", exe_name_clean,
            "--distpath", output_dir,
            "--workpath", os.path.join(self.temp_dir, "build"),
            "--specpath", self.temp_dir,
        ]
        
        if icon_path and os.path.exists(icon_path):
            cmd.extend(["--icon", icon_path])
        
        cmd.append(self.source_file)
        
        clean_cmd = [str(x) for x in cmd if x]
        cmd_str = ' '.join(clean_cmd)
        print(f"[*] PyInstaller 命令: {cmd_str}")
        
        if log_callback:
            log_callback(f"PyInstaller 命令: {cmd_str}", "info")
        
        try:
            print(f"[*] 启动 PyInstaller 核心编译...")
            print(f"[*] 工作目录: {self.temp_dir}")
            print(f"[*] 输出目录: {output_dir}")
            
            if log_callback:
                log_callback("启动 PyInstaller 核心编译...", "info")
                log_callback(f"工作目录: {self.temp_dir}", "info")
                log_callback(f"输出目录: {output_dir}", "info")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors='replace',
                bufsize=1
            )
            
            output_lines = []
            while process.poll() is None:
                ready, _, _ = select.select([process.stdout], [], [], 0.1)
                if ready:
                    line = process.stdout.readline()
                    if line:
                        stripped = line.strip()
                        output_lines.append(stripped)
                        print(f"[PyInstaller] {stripped}")
                        if log_callback:
                            log_callback(stripped, "verbose")
            
            process.wait()
            
            if process.returncode == 0:
                print(f"[+] 编译成功！")
                if log_callback:
                    log_callback("编译成功！", "success")
                return True
            else:
                last_lines = "\n".join(output_lines[-20:])
                error_summary = f"编译失败，返回码: {process.returncode}\n最后20行日志:\n{last_lines}"
                print(f"[-] 编译失败，返回码: {process.returncode}")
                print(f"[-] 编译日志:\n" + "\n".join(output_lines[-20:]))
                if log_callback:
                    log_callback(error_summary, "error")
                return False
        except Exception as e:
            print(f"[-] 引擎错误: {repr(e)}")
            if log_callback:
                log_callback(f"引擎错误: {repr(e)}", "error")
            return False
        finally:
            self._cleanup()

    def _cleanup(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass