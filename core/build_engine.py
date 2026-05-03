# ======================================================================
# 功能模块：构建引擎 (Build Engine)
# ======================================================================

# core/build_engine.py
import os
import subprocess
import tempfile
import shutil

class BuildEngine:
    def __init__(self):
        # 创建系统级临时目录用于存放编译文件，避免污染用户工作区
        self.temp_dir = tempfile.mkdtemp(prefix="script_pilot_")
        self.source_file = os.path.join(self.temp_dir, "launcher_proxy.py")

    def build_exe(self, source_code: str, output_dir: str, exe_name: str, icon_path: str = None) -> bool:
        """
        调用 PyInstaller 编译源码为 EXE。
        
        :param source_code: 生成的 Python 源码字符串
        :param output_dir: 生成的 EXE 存放目录
        :param exe_name: EXE 的最终名称 (无需加 .exe)
        :param icon_path: 可选的 .ico 图标路径
        :return: bool, 编译是否成功
        """
        # 1. 写入源码到临时文件
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write(source_code)
            
        # 2. 组装 PyInstaller 编译命令
        # -F: 单文件模式 | -w: 隐藏控制台 | --noconfirm: 覆盖输出 | --clean: 清理缓存
        cmd =[
            "pyinstaller", 
            "-F", 
            "-w", 
            "--noconfirm", 
            "--clean",
            f"--name={exe_name}",
            f"--distpath={output_dir}",
            f"--workpath={os.path.join(self.temp_dir, 'build')}",
            f"--specpath={self.temp_dir}"
        ]
        
        if icon_path and os.path.exists(icon_path):
            cmd.append(f"--icon={icon_path}")
            
        cmd.append(self.source_file)

        # 3. 执行编译 (阻塞式，后续在 UI 中需放入子线程运行)
        try:
            print(f"[*] 开始编译: {exe_name}.exe")
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                encoding='utf-8'
            )
            
            if process.returncode == 0:
                print(f"[+] 编译成功！输出路径: {os.path.join(output_dir, exe_name + '.exe')}")
                return True
            else:
                print(f"[-] 编译失败。错误日志:\n{process.stdout}")
                return False
                
        except FileNotFoundError:
            print("[-] 致命错误: 未找到 PyInstaller。请确保已在当前环境中执行 'pip install pyinstaller'。")
            return False
        finally:
            self._cleanup()

    def _cleanup(self):
        """清理临时编译目录"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            pass # 忽略清理错误