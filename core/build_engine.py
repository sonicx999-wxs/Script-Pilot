# ======================================================================
# 功能模块：构建引擎 (Build Engine)
# ======================================================================
# 核心改动：加入 build_pyw 方法，实现瞬间生成单文件；保留 build_exe 供独立打包使用。
# ======================================================================

# core/build_engine.py
import os
import sys
import subprocess
import tempfile
import shutil

class BuildEngine:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="script_pilot_")
        self.source_file = os.path.join(self.temp_dir, "launcher_proxy.py")

    def build_pyw(self, source_code: str, output_dir: str, exe_name: str) -> bool:
        """生成极轻量级的 .pyw 智能启动器 (瞬间完成)"""
        try:
            # 验证输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            if not os.access(output_dir, os.W_OK):
                print(f"[-] 无法写入目录: {output_dir}")
                return False
            
            pyw_path = os.path.join(output_dir, f"{exe_name}.pyw")
            with open(pyw_path, 'w', encoding='utf-8') as f:
                f.write(source_code)
            print(f"[+] 智能启动器生成成功！路径: {pyw_path}")
            return True
        except Exception as e:
            print(f"[-] 生成 .pyw 失败: {repr(e)}")
            return False

    def build_exe(self, source_code: str, output_dir: str, exe_name: str, icon_path: str = None) -> bool:
        """生成独立 EXE (PyInstaller)"""
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
            
        cmd =[
            sys.executable, "-m", "PyInstaller", 
            "--onefile",
            "--windowed",
            "--noconfirm", 
            "--clean",
            "--hidden-import=six",
            "--hidden-import=wx",
            f"--name={exe_name}",
            f"--distpath={output_dir}",
            f"--workpath={os.path.join(self.temp_dir, 'build')}",
            f"--specpath={self.temp_dir}"
        ]
        
        if icon_path and os.path.exists(icon_path):
            cmd.append(f"--icon={icon_path}")
            
        cmd.append(self.source_file)

        try:
            print(f"[*] 启动 PyInstaller 核心编译...")
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                errors='replace' 
            )
            
            if process.returncode == 0:
                print(f"[+] 编译成功！")
                return True
            else:
                print(f"[-] 编译失败日志:\n{process.stdout}")
                return False
        except Exception as e:
            print(f"[-] 引擎错误: {repr(e)}")
            return False
        finally:
            self._cleanup()

    def _cleanup(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass