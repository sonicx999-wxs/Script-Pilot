# ======================================================================
# 功能模块：代理代码生成器 (Agent Code Generator)
# ======================================================================

# core/code_generator.py
import os

def generate_proxy_code(metadata: dict, params: list) -> str:
    """
    动态生成 Gooey 代理启动器源码。
    
    :param metadata: dict, 包含 title, description, venv_path, script_path
    :param params: list, 包含标准 JSON 格式的参数列表
    :return: str, 完整的 Python 源码字符串
    """
    
    # 1. 提取元数据并处理路径转义 (防止 Windows 路径反斜杠报错)
    title = metadata.get('title', '未命名启动器')
    desc = metadata.get('description', '由 Script-Pilot 自动生成')
    venv_path = metadata.get('venv_path', '').replace('\\', '\\\\')
    script_path = metadata.get('script_path', '').replace('\\', '\\\\')

    # 2. 动态构建 argparse 控件代码与命令组装代码
    arg_lines = ""
    cmd_assembly_lines = ""
    
    for p in params:
        flag_name = p.get('name') # 例如 '--url'
        widget = p.get('widget', 'TextField')
        help_text = p.get('help', '')
        required = p.get('required', False)
        default = p.get('default', '')
        
        # 构建 add_argument 语句
        req_str = "True" if required else "False"
        def_str = f", default='{default}'" if default else ""
        arg_lines += f"    parser.add_argument('{flag_name}', help='{help_text}', required={req_str}{def_str}, widget='{widget}')\n"
        
        # 构建 subprocess 命令组装语句 (将 argparse 解析后的值还原为命令行参数)
        dest_name = flag_name.lstrip('-').replace('-', '_') # '--input-file' -> 'input_file'
        cmd_assembly_lines += f"    if getattr(args, '{dest_name}', None):\n"
        cmd_assembly_lines += f"        cmd.extend(['{flag_name}', str(getattr(args, '{dest_name}'))])\n"

    # 3. 注入母版模板 (Template Injection)
    template = f'''# -*- coding: utf-8 -*-
# 此文件由 Script-Pilot v0.1.0-alpha 自动生成
import argparse
import subprocess
import sys
from gooey import Gooey, GooeyParser

@Gooey(
    program_name="{title}", 
    program_description="{desc}", 
    clear_before_run=True, 
    language='chinese',
    default_size=(700, 550)
)
def main():
    parser = GooeyParser(description="请在下方填写运行参数：")
    
    # === 动态参数注入区 ===
{arg_lines}
    args = parser.parse_args()

    # === 核心调度引擎 ===
    cmd =["{venv_path}", "{script_path}"]
{cmd_assembly_lines}

    print(f"[*] 正在挂载独立虚拟环境...", flush=True)
    print(f"[*] 执行命令: {{' '.join(cmd)}}\\n" + "-"*40, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8',
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end='', flush=True)
            
        process.wait()
        
        if process.returncode == 0:
            print("\\n[+] 任务执行成功结束。", flush=True)
        else:
            print(f"\\n[-] 任务异常终止，退出码: {{process.returncode}}", flush=True)
            sys.exit(process.returncode)
            
    except Exception as e:
        print(f"\\n[!] 启动器致命错误: {{str(e)}}", flush=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
    return template